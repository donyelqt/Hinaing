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
from ...schemas.rag import AugmentedContext
from ...schemas.query import QueryPlan
from .agents import (
    RetrievalAgent,
    SentimentAgent,
    CredibilityAgent,
    ThemeRouterAgent,
)
from ..agents.query_orchestrator import QueryOrchestratorAgent
from ..agents.context_agent import ContextAugmentationAgent
from ..langsearch import LangSearchClient
from ..nlp.gemini import gemini_client, GeminiClient
from ..agents.gemini import run_gemini_agent
# Note: build_focus_query and get_window_timedelta removed - query building now handled by QueryOrchestratorAgent
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
    augmented_contexts: dict[str, AugmentedContext]
    theme_insights: list[Insight]
    credibility_notes: dict[str, float]
    retrieval_plan: QueryPlan
    snapshot: SnapshotResponse


THEME_GROUPS = {
    "infrastructure": {
        "label": "Infrastructure",
        "focus_values": {"infrastructure"},
        "keywords": {
            "road",
            "traffic",
            "water",
            "power",
            "infrastructure",
            "bridge",
            "construction",
        },
    },
    "health": {
        "label": "Health & Wellness",
        "focus_values": {"health"},
        "keywords": {
            "hospital",
            "clinic",
            "health",
            "dengue",
            "covid",
            "medicine",
            "vaccine",
            "wellness",
        },
    },
    "safety": {
        "label": "Public Safety",
        "focus_values": {"safety"},
        "keywords": {
            "crime",
            "police",
            "fire",
            "landslide",
            "safety",
            "accident",
            "emergency",
            "security",
        },
    },
    "tourism": {
        "label": "Tourism & Events",
        "focus_values": {"tourism"},
        "keywords": {
            "tourism",
            "tourist",
            "hotel",
            "festival",
            "event",
            "panagbenga",
            "visitor",
        },
    },
    "economy": {
        "label": "Business & Economy",
        "focus_values": {"economy", "business"},
        "keywords": {
            "market",
            "vendor",
            "livelihood",
            "economy",
            "business",
            "investment",
            "mallification",
            "sm prime",
            "price",
        },
    },
    "environment": {
        "label": "Environment",
        "focus_values": {"environment"},
        "keywords": {
            "garbage",
            "pollution",
            "environment",
            "rain",
            "waste",
            "tree",
            "green",
            "climate",
        },
    },
}

set_theme_groups(THEME_GROUPS)


retrieval_agent = RetrievalAgent()
sentiment_agent = SentimentAgent()
credibility_agent_node = CredibilityAgent()
theme_router_agent = ThemeRouterAgent()
query_orchestrator = QueryOrchestratorAgent()


async def orchestrate_queries(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    try:
        plan = query_orchestrator.run(request)
    except Exception as exc:
        logger.warning("[snapshot] Query orchestrator failed, falling back: %s", exc)
        plan = None
    state["retrieval_plan"] = plan
    return state


async def fetch_documents(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    plan = state.get("retrieval_plan")
    logger.info("[snapshot] Retrieval agent planning fetch", extra={"platforms": request.platforms})
    start_time = time.perf_counter()
    try:
        documents = await retrieval_agent.run(request, query_plan=plan)
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


async def augment_context(state: SnapshotState) -> SnapshotState:
    """Augment theme context using RAG pipeline."""
    theme_docs = state.get("theme_documents") or {}
    if not theme_docs:
        state["augmented_contexts"] = {}
        logger.info("[snapshot] augment_context skipped (no theme docs)")
        return state

    # Use the shared source of truth from agent_tools to avoid split-brain during reloads
    from . import agent_tools
    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS
    
    request = state["request"]

    # Determine active themes based on focus areas
    active_themes = set(current_theme_groups.keys())
    if request.focus_areas:
        requested_focus = {f.lower() for f in request.focus_areas}
        matched_themes = {
            key for key, meta in current_theme_groups.items()
            if requested_focus & meta.get("focus_values", set())
        }
        if matched_themes:
            active_themes = matched_themes

    agent = ContextAugmentationAgent()
    augmented: dict[str, AugmentedContext] = {}

    for theme_key, docs in theme_docs.items():
        if not docs or theme_key not in active_themes:
            continue
        meta = current_theme_groups.get(theme_key)
        label = meta["label"] if meta else theme_key.title()
        try:
            context = await agent.augment_context(
                documents=docs,
                theme=label,
                time_window=request.time_window,
                top_k=10,
            )
            augmented[theme_key] = context
        except Exception as exc:
            logger.warning("[snapshot] augment_context failed for %s: %s", label, exc)

    state["augmented_contexts"] = augmented
    logger.info("[snapshot] RAG augmented context for %d themes", len(augmented))
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


# Minimum average relevance score to generate insights for a theme
# Lowered from 0.55 to 0.40 to allow more results through RAG filtering
MIN_RELEVANCE_THRESHOLD = 0.40


def _synthesize_single_theme(
    theme_key: str,
    docs: list[WebDocument],
    contexts: dict[str, AugmentedContext] | None,
) -> Insight | None:
    """Synthesize insight for a single theme."""
    from . import agent_tools
    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS
    meta = current_theme_groups.get(theme_key)
    label = meta["label"] if meta else theme_key.title()
    context = (contexts or {}).get(theme_key)

    # Check relevance threshold - skip themes with low relevance
    if context and context.relevance_scores:
        avg_score = sum(context.relevance_scores) / len(context.relevance_scores)
        if avg_score < MIN_RELEVANCE_THRESHOLD:
            logger.info(
                f"[theme_insight] Skipping '{label}' - low relevance (avg={avg_score:.3f} < {MIN_RELEVANCE_THRESHOLD})"
            )
            return None

    if context and context.relevant_chunks:
        top_chunks = context.relevant_chunks[:25]
        top_scores = context.relevance_scores[: len(top_chunks)]
        enriched_docs = [
            {
                "title": chunk.source_title,
                "snippet": chunk.content,
                "url": str(chunk.source_url) if chunk.source_url else "",
                "relevance_score": score,
            }
            for chunk, score in zip(top_chunks, top_scores)
        ]
    else:
        # Ensure URL is string (HttpUrl -> str) for theme agent
        enriched_docs = [
            {
                **doc.model_dump(),
                "url": str(doc.url) if doc.url else "",
            }
            for doc in docs[:25]
        ]

    evidence_seed = [str(doc.url) for doc in docs[:3] if doc.url]
    try:
        if len(docs) < 2:
            raise ValueError("skip_gemini_fallback")
        from ..agents.theme_agent import run_theme_agent

        prompt = (
            "You are a civic operations analyst for Baguio City. "
            f"Focus on the theme '{label}'. "
            "Write JSON with keys 'title', 'detail', 'evidence' (array of source URLs). "
            "Highlight actionable risk or opportunity from the provided documents."
        )
        response = run_theme_agent(
            theme_label=label,
            prompt=prompt,
            documents=enriched_docs,
        )
        parsed = _parse_agent_json(response)
        evidence = evidence_seed
        if parsed:
            title = parsed.get("title") or f"Key updates in {label}"
            detail = parsed.get("detail") or "Context unavailable"
            parsed_evidence = parsed.get("evidence")
            if isinstance(parsed_evidence, list) and parsed_evidence:
                # Filter out placeholder text and empty strings
                valid_urls = [
                    str(item) for item in parsed_evidence 
                    if item and str(item).startswith("http")
                ]
                if valid_urls:
                    evidence = valid_urls
                # If LLM returned invalid URLs, fall back to evidence_seed
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
    except Exception as exc:
        logger.warning("Theme agent failed for %s: %s", label, exc)
        fallback_doc = docs[0]
        return Insight(
            category=label,
            title=f"Key updates in {label}",
            detail=(fallback_doc.snippet or fallback_doc.title or "Context unavailable")[:240],
            evidence=[str(doc.url) for doc in docs[:2] if doc.url],
        )


def theme_agents(state: SnapshotState) -> SnapshotState:
    """Run Gemini mini-agents per theme to craft insights in parallel."""
    theme_docs = state.get("theme_documents", {})
    contexts = state.get("augmented_contexts", {})
    request = state["request"]
    start_time = time.perf_counter()

    from . import agent_tools
    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS

    # Determine active themes based on focus areas
    active_themes = set(current_theme_groups.keys())
    if request.focus_areas:
        requested_focus = {f.lower() for f in request.focus_areas}
        # Find themes that have at least one matching focus value
        matched_themes = {
            key for key, meta in current_theme_groups.items()
            if requested_focus & meta.get("focus_values", set())
        }
        # If we found matches, strictly filter. If no matches (e.g. "general"), 
        # we might want to keep all, but here we strictly respect the user's filter 
        # if they provided specific known categories.
        if matched_themes:
            active_themes = matched_themes
        
        logger.info(
            "[snapshot] Filtering themes by focus areas: %s -> %s", 
            request.focus_areas, active_themes
        )

    # Prepare tasks for parallel execution
    tasks = []
    for theme_key, docs in theme_docs.items():
        if docs and theme_key in active_themes:
            tasks.append((theme_key, docs))
    
    # Run all theme agents in parallel using threads
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    insights = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_synthesize_single_theme, theme_key, docs, contexts): theme_key
            for theme_key, docs in tasks
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if isinstance(result, Insight):
                    insights.append(result)
            except Exception as exc:
                theme_key = futures[future]
                logger.exception("Theme agent task failed for %s: %s", theme_key, exc)
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


def _build_query(request: SnapshotRequest) -> str:
    """Build a search query for semantic reranking."""
    focus = " ".join(request.focus_areas or ["civic updates"])
    return f"Baguio City {focus} {request.time_window}"


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

    # Primary: Use theme insights which are already balanced by theme
    insights: list[Insight] = []
    theme_fallbacks = state.get("theme_insights") or []
    
    if theme_fallbacks:
        # Use theme insights as primary source (they're already balanced)
        logger.info("[snapshot] Using %d theme-generated insights", len(theme_fallbacks))
        insights.extend(theme_fallbacks[:3])
    elif insights_payload:
        # Only use Gemini insights if no theme insights available
        logger.info("[snapshot] Using %d Gemini-generated insights", len(insights_payload))
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
        # Last resort: generate basic insights from focus areas
        logger.info("[snapshot] Generating fallback insights from focus areas")
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
graph.add_node("orchestrate_queries", orchestrate_queries)
graph.add_node("fetch_documents", fetch_documents)
graph.add_node("label_sentiment", label_sentiment)
graph.add_node("analyze_enriched", analyze_enriched)
graph.add_node("theme_agents", theme_agents)
graph.add_node("augment_context", augment_context)
graph.add_node("build_snapshot", build_snapshot)

graph.add_edge(START, "orchestrate_queries")
graph.add_edge("orchestrate_queries", "fetch_documents")
graph.add_edge("fetch_documents", "label_sentiment")
graph.add_edge("label_sentiment", "analyze_enriched")
graph.add_edge("analyze_enriched", "augment_context")
graph.add_edge("augment_context", "theme_agents")
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
