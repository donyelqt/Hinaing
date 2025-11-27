"""LangGraph workflow for generating sentiment snapshots."""

from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
import asyncio
from pydantic import ValidationError

from ...core.config import get_settings
from ...schemas.snapshot import (
    Insight,
    SentimentBreakdown,
    SnapshotRequest,
    SnapshotResponse,
    WebDocument,
)
from .agents import (
    RetrievalAgent,
    SentimentAgent,
    CredibilityAgent,
    ThemeRouterAgent,
)
from ..langsearch import LangSearchClient
from ..nlp.gemini import gemini_client, GeminiClient
from ..agents.gemini import run_gemini_agent
from .tools import (
    build_focus_query,
    get_window_timedelta,
)
from .agent_tools import set_theme_groups

settings = get_settings()
logger = logging.getLogger(__name__)
if settings.langsmith_api_key:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    if settings.langsmith_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)


class SnapshotState(TypedDict, total=False):
    request: SnapshotRequest
    documents: list[WebDocument]
    enriched: list[WebDocument]
    theme_documents: dict[str, list[WebDocument]]
    theme_insights: list[Insight]
    credibility_notes: dict[str, float]
    retrieval_plan: dict[str, Any]
    snapshot: SnapshotResponse


THEME_GROUPS = {
    "health_safety": {
        "label": "Health & Safety",
        "focus_values": {"health", "safety"},
        "keywords": {
            "hospital",
            "clinic",
            "health",
            "dengue",
            "covid",
            "crime",
            "police",
            "fire",
            "landslide",
            "safety",
        },
    },
    "infra_env": {
        "label": "Infrastructure & Environment",
        "focus_values": {"infrastructure", "environment"},
        "keywords": {
            "road",
            "traffic",
            "water",
            "power",
            "garbage",
            "infrastructure",
            "pollution",
            "environment",
            "rain",
        },
    },
    "tourism_econ": {
        "label": "Tourism & Economy",
        "focus_values": {"tourism", "economy"},
        "keywords": {
            "tourism",
            "tourist",
            "hotel",
            "market",
            "vendor",
            "livelihood",
            "economy",
            "mallification",
            "sm prime",
        },
    },
}

set_theme_groups(THEME_GROUPS)


retrieval_agent = RetrievalAgent()
sentiment_agent = SentimentAgent()
credibility_agent_node = CredibilityAgent()
theme_router_agent = ThemeRouterAgent()


def _build_query(request: SnapshotRequest) -> str:
    return build_focus_query(request)


def _get_window_timedelta(time_window: str | None) -> timedelta | None:
    return get_window_timedelta(time_window)


async def fetch_documents(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    logger.info("[snapshot] Retrieval agent planning fetch", extra={"platforms": request.platforms})
    start_time = time.perf_counter()
    try:
        documents = await retrieval_agent.run(request)
    except Exception:
        logger.exception("Retrieval agent failed; returning empty document set")
        documents = []

    if "web" in request.platforms and "facebook" in request.platforms and len(documents) > 1:
        query = _build_query(request)
        try:
            reranker = LangSearchClient()
            documents = await reranker.rerank(query=query, documents=documents)
        except Exception as exc:
            logger.warning("Semantic rerank failed; continuing without rerank: %s", exc)

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("[snapshot] Retrieval agent completed in %.1f ms with %d docs", duration_ms, len(documents))
    state["documents"] = documents
    return state


def label_sentiment(state: SnapshotState) -> SnapshotState:
    start_time = time.perf_counter()
    docs = state.get("documents", [])
    state["enriched"] = sentiment_agent.run(docs)
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("[snapshot] Sentiment agent labeled %d docs in %.1f ms", len(docs), duration_ms)
    return state


async def analyze_enriched(state: SnapshotState) -> SnapshotState:
    docs = state.get("enriched") or []
    request = state["request"]
    start_time = time.perf_counter()
    if not docs:
        state["credibility_notes"] = {}
        state["theme_documents"] = {key: [] for key in THEME_GROUPS}
        logger.info("[snapshot] analyze_enriched skipped (no docs)")
        return state

    credibility_task = asyncio.to_thread(credibility_agent_node.run, docs)
    theme_task = asyncio.to_thread(theme_router_agent.run, docs, request)
    credibility_notes, theme_docs = await asyncio.gather(credibility_task, theme_task)
    state["credibility_notes"] = credibility_notes
    state["theme_documents"] = theme_docs
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "[snapshot] analyze_enriched processed %d docs in %.1f ms",
        len(docs),
        duration_ms,
    )
    return state


def _parse_agent_json(raw_text: str) -> dict[str, str] | None:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        inner = text.split("\n", 1)
        text = inner[1] if len(inner) > 1 else text[3:]
        text = text[:-3].strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        logger.debug("Theme agent response not JSON: %s", raw_text)
    return None


def _synthesize_theme_insight(label: str, docs: list[WebDocument]) -> Insight:
    context_docs = [doc.model_dump() for doc in docs[:5]]
    prompt = (
        "You are a civic operations analyst for Baguio City. "
        f"Focus on the theme '{label}'. "
        "Write JSON with keys 'title', 'detail', 'evidence' (array of source URLs). "
        "Highlight actionable risk or opportunity from the provided documents."
    )
    response = run_gemini_agent(prompt, documents=context_docs)
    parsed = _parse_agent_json(response)
    evidence = [str(doc.url) for doc in docs[:3] if doc.url]
    if parsed:
        title = parsed.get("title") or f"Key updates in {label}"
        detail = parsed.get("detail") or "Context unavailable"

settings = get_settings()
logger = logging.getLogger(__name__)
if settings.langsmith_api_key:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    if settings.langsmith_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)


class SnapshotState(TypedDict, total=False):
    request: SnapshotRequest
    documents: list[WebDocument]
    enriched: list[WebDocument]
    theme_documents: dict[str, list[WebDocument]]
    theme_insights: list[Insight]
    credibility_notes: dict[str, float]
    retrieval_plan: dict[str, Any]
    snapshot: SnapshotResponse


THEME_GROUPS = {
    "health_safety": {
        "label": "Health & Safety",
        "focus_values": {"health", "safety"},
        "keywords": {
            "hospital",
            "clinic",
            "health",
            "dengue",
            "covid",
            "crime",
            "police",
            "fire",
            "landslide",
            "safety",
        },
    },
    "infra_env": {
        "label": "Infrastructure & Environment",
        "focus_values": {"infrastructure", "environment"},
        "keywords": {
            "road",
            "traffic",
            "water",
            "power",
            "garbage",
            "infrastructure",
            "pollution",
            "environment",
            "rain",
        },
    },
    "tourism_econ": {
        "label": "Tourism & Economy",
        "focus_values": {"tourism", "economy"},
        "keywords": {
            "tourism",
            "tourist",
            "hotel",
            "market",
            "vendor",
            "livelihood",
            "economy",
            "mallification",
            "sm prime",
        },
    },
}


def _build_query(request: SnapshotRequest) -> str:
    return build_focus_query(request)


def _get_window_timedelta(time_window: str | None) -> timedelta | None:
    return get_window_timedelta(time_window)


async def fetch_documents(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    logger.info("[snapshot] Retrieval agent planning fetch", extra={"platforms": request.platforms})
    try:
        documents = await retrieval_agent.run(request)
    except Exception:
        logger.exception("Retrieval agent failed; returning empty document set")
        documents = []

    if "web" in request.platforms and "facebook" in request.platforms and len(documents) > 1:
        query = _build_query(request)
        try:
            reranker = LangSearchClient()
            documents = await reranker.rerank(query=query, documents=documents)
        except Exception as exc:
            logger.warning("Semantic rerank failed; continuing without rerank: %s", exc)

    state["documents"] = documents
    return state


    state["theme_documents"] = route_documents_by_theme(docs, state["request"].focus_areas)
    return state


def _parse_agent_json(raw_text: str) -> dict[str, str] | None:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        inner = text.split("\n", 1)
        text = inner[1] if len(inner) > 1 else text[3:]
        text = text[:-3].strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        logger.debug("Theme agent response not JSON: %s", raw_text)
    return None


def _synthesize_theme_insight(label: str, docs: list[WebDocument]) -> Insight:
    context_docs = [doc.model_dump() for doc in docs[:5]]
    prompt = (
        "You are a civic operations analyst for Baguio City. "
        f"Focus on the theme '{label}'. "
        "Write JSON with keys 'title', 'detail', 'evidence' (array of source URLs). "
        "Highlight actionable risk or opportunity from the provided documents."
    )
    response = run_gemini_agent(prompt, documents=context_docs)
    parsed = _parse_agent_json(response)
    evidence = [str(doc.url) for doc in docs[:3] if doc.url]
    if parsed:
        title = parsed.get("title") or f"Key updates in {label}"
        detail = parsed.get("detail") or "Context unavailable"
        parsed_evidence = parsed.get("evidence")
        if isinstance(parsed_evidence, list) and parsed_evidence:
            evidence = [str(item) for item in parsed_evidence if item]
    else:
        fallback_doc = max(
            docs,
            key=lambda d: (d.metadata or {}).get("semantic_relevance_score", 0.0),
            default=docs[0],
        )
        title = f"Key updates in {label}"
        detail = (fallback_doc.snippet or fallback_doc.title or "Context unavailable")[:240]
    return Insight(
        category=label,
        title=title,
        detail=detail[:240],
        evidence=evidence,
    )


def theme_agents(state: SnapshotState) -> SnapshotState:
    """Run Gemini mini-agents per theme to craft insights."""
    theme_docs = state.get("theme_documents", {})
    insights: list[Insight] = []
    start_time = time.perf_counter()

    for theme_key, docs in theme_docs.items():
        if not docs:
            continue
        meta = THEME_GROUPS.get(theme_key)
        label = meta["label"] if meta else theme_key.title()
        try:
            if len(docs) < 2:
                raise ValueError("skip_gemini_fallback")
            insight = _synthesize_theme_insight(label, docs)
            insights.append(insight)
        except Exception as exc:
            logger.warning("Theme agent failed for %s: %s", label, exc)
            fallback_doc = docs[0]
            insights.append(
                Insight(
                    category=label,
                    title=f"Key updates in {label}",
                    detail=(fallback_doc.snippet or fallback_doc.title or "Context unavailable")[:240],
                    evidence=[str(doc.url) for doc in docs[:2] if doc.url],
                )
            )
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "[snapshot] Theme agents generated %d insights in %.1f ms", len(insights), duration_ms
    )
    state["theme_insights"] = insights
    return state


def _derive_label(scores: dict[str, float]) -> str:
    negative = scores.get("negative", 0)
    positive = scores.get("positive", 0)
    if negative >= 0.55:
        return "Highly Concerned"
    if negative >= 0.4:
        return "Moderately Concerned"
    if positive >= 0.5:
        return "Positive Momentum"
    return "Mixed Sentiment"


summary_chain = RunnableLambda(
    lambda data: (
        f"Public chatter over {data['window']} centers on {', '.join(data['topics']) or 'civic services'}. "
        f"Representative updates cite {data['examples']}."
    )
)


async def build_snapshot(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    docs = state.get("enriched", [])
    logger.info(
        "[snapshot] Building snapshot",
        extra={
            "platforms": request.platforms,
            "time_window": request.time_window,
            "focus_areas": request.focus_areas,
            "doc_count": len(docs),
        },
    )
    total = max(len(docs), 1)
    counts = Counter(doc.sentiment or "neutral" for doc in docs)
    scores = {
        "negative": counts.get("negative", 0) / total,
        "neutral": counts.get("neutral", 0) / total,
        "positive": counts.get("positive", 0) / total,
    }

    summary_text = None
    insights_payload: list[dict[str, str]] = []
    if gemini_client.is_available and docs:
        logger.info("[snapshot] Invoking Gemini for narrative", extra={"docs_used": len(docs)})
        try:
            summary_text, insights_payload = await gemini_client.analyze_snapshot(
                window=request.time_window,
                focus_areas=request.focus_areas,
                documents=[doc.model_dump() for doc in docs],
            )
            logger.info("[snapshot] Gemini call completed successfully")
        except Exception as exc:
            logger.exception("[snapshot] Gemini call failed: %s", exc)
            summary_text = None
            insights_payload = []

    if not summary_text:
        logger.info("[snapshot] Using fallback summary chain")
        summary_text = summary_chain.invoke(
            {
                "window": request.time_window,
                "topics": request.focus_areas or ["public services"],
                "examples": "; ".join(doc.title for doc in docs[:2]) or "limited recent updates",
            }
        )
    logger.info("[snapshot] Summary text ready: %s", summary_text[:100] if summary_text else "None")

    insights: list[Insight] = []
    if insights_payload:
        for idx, payload in enumerate(insights_payload[:3], start=1):
            try:
                evidence_raw = payload.get("evidence")
                match evidence_raw:
                    case str() as value:
                        evidence = [value]
                    case list() as values:
                        evidence = [str(item) for item in values if item]
                    case _:
                        evidence = []

                insights.append(
                    Insight(
                        category=(payload.get("category") or "Operations").strip() or "Operations",
                        title=payload.get("title") or f"Key development {idx}",
                        detail=payload.get("detail") or "",
                        evidence=evidence,
                    )
                )
            except ValidationError as exc:  # pragma: no cover - defensive against LLM drift
                logger.debug("Skipping malformed Gemini insight: %s", exc)
                continue
    else:
        theme_fallbacks = state.get("theme_insights") or []
        if theme_fallbacks:
            insights.extend(theme_fallbacks[:3])
        else:
            for focus in (request.focus_areas or ["Operations"]):
                related = [doc for doc in docs if focus.lower() in (doc.snippet.lower() + doc.title.lower())]
                snippet = related[0].snippet if related else (docs[0].snippet if docs else "Residents request timely advisories.")
                insights.append(
                    Insight(
                        category=focus.title(),
                        title=f"Monitor {focus.title()} developments",
                        detail=snippet[:240],
                        evidence=[str(doc.url) for doc in related[:2] if doc.url],
                    )
                )
                if len(insights) >= 3:
                    break

    alerts: list[str] | None = None
    if request.include_alerts and scores["negative"] >= 0.45:
        alerts = [
            "Elevated negative sentiment detected—prioritize rapid response coordination.",
        ]

    logger.info("[snapshot] Creating SnapshotResponse with %d insights", len(insights))
    try:
        snapshot = SnapshotResponse(
            overall_sentiment=SentimentBreakdown(
                label=_derive_label(scores),
                summary=summary_text,
                scores=scores,
            ),
            actionable_insights=insights,
            alerts=alerts,
            sources=docs,
        )
        logger.info("[snapshot] SnapshotResponse created successfully")
    except Exception as exc:
        logger.exception("[snapshot] Failed to create SnapshotResponse: %s", exc)
        raise

    state["snapshot"] = snapshot
    logger.info("[snapshot] build_snapshot completed successfully")
    return state


graph = StateGraph(SnapshotState)
graph.add_node("fetch_documents", fetch_documents)
graph.add_node("label_sentiment", label_sentiment)
graph.add_node("analyze_enriched", analyze_enriched)
graph.add_node("theme_agents", theme_agents)
graph.add_node("build_snapshot", build_snapshot)

graph.add_edge(START, "fetch_documents")
graph.add_edge("fetch_documents", "label_sentiment")
graph.add_edge("label_sentiment", "analyze_enriched")
graph.add_edge("analyze_enriched", "theme_agents")
graph.add_edge("theme_agents", "build_snapshot")
graph.add_edge("build_snapshot", END)

compiled_graph = graph.compile()


async def generate_snapshot(request: SnapshotRequest) -> SnapshotResponse:
    logger.info(
        "[snapshot] generate_snapshot invoked",
        extra={
            "platforms": request.platforms,
            "time_window": request.time_window,
            "focus_areas": request.focus_areas,
            "include_alerts": request.include_alerts,
        },
    )
    state: SnapshotState = {"request": request}
    result = await compiled_graph.ainvoke(state)
    snapshot = result.get("snapshot")
    if snapshot is None:
        return SnapshotResponse(
            overall_sentiment=SentimentBreakdown(
                label="No Data",
                summary="No recent documents were available for the selected configuration.",
                scores={"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            ),
            actionable_insights=[],
            alerts=None,
            sources=[],
        )
    return snapshot
