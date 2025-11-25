"""LangGraph workflow for generating sentiment snapshots."""

from __future__ import annotations

import logging
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from ...core.config import get_settings
from ...schemas.snapshot import (
    Insight,
    SentimentBreakdown,
    SnapshotRequest,
    SnapshotResponse,
    WebDocument,
)
from ..langsearch import LangSearchClient
from ..nlp.gemini import gemini_client

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
    snapshot: SnapshotResponse


def _build_query(request: SnapshotRequest) -> str:
    # Always include Baguio City context for local relevance
    base_location = "Baguio City Philippines"
    
    # Focus on emerging concerns, issues, and current problems
    concern_keywords = [
        "concerns", "issues", "problems", "complaints", 
        "challenges", "crisis", "emergency", "urgent",
        "residents complain", "citizens report", "community issues",
        "mallification public market", "SM Baguio public market"
    ]
    # Map Step 3 themes (focus_areas) to richer domain-specific keyword sets
    focus_keywords: dict[str, list[str]] = {
        "infrastructure": [
            "infrastructure",
            "roads",
            "traffic",
            "congestion",
            "potholes",
            "public transport",
            "jeepney",
            "terminal",
            "water supply",
            "water interruption",
            "power outage",
            "brownout",
            "garbage collection",
        ],
        "health": [
            "health",
            "wellness",
            "hospital",
            "clinic",
            "health center",
            "public health",
            "gastroenteritis",
            "diarrhea",
            "food poisoning",
            "sanitation",
        ],
        "safety": [
            "public safety",
            "crime",
            "police",
            "fire",
            "flood",
            "landslide",
            "evacuation",
            "911 hotline",
            "emergency response",
            "disaster risk",
        ],
        "tourism": [
            "tourism",
            "tourists",
            "visitors",
            "hotel occupancy",
            "Panagbenga",
            "Burnham Park",
            "Session Road",
            "tourist complaints",
            "tourist experience",
        ],
        "economy": [
            "business",
            "economy",
            "vendors",
            "market",
            "public market",
            "SM Baguio",
            "employment",
            "livelihood",
            "investment",
        ],
        "environment": [
            "environment",
            "air quality",
            "pollution",
            "waste",
            "garbage",
            "solid waste",
            "forest",
            "parks",
            "climate",
            "flooding",
        ],
    }

    if request.focus_areas:
        # Expand each selected theme into a richer set of keywords
        expanded_terms: list[str] = []
        for area in request.focus_areas:
            expanded_terms.extend(focus_keywords.get(area, [area]))

        # De-duplicate while keeping order reasonably stable
        seen: set[str] = set()
        unique_terms: list[str] = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        focus_terms = " OR ".join(unique_terms)
        concern_terms = " OR ".join(concern_keywords)
        query = f"({focus_terms}) AND ({concern_terms}) AND ({base_location} OR Baguio OR Cordillera)"
    else:
        # Default to emerging concerns and public sentiment in Baguio
        concern_terms = " OR ".join(concern_keywords)
        query = f"({concern_terms}) AND (public sentiment OR community) AND {base_location}"
    
    return query


def _get_window_timedelta(time_window: str | None) -> timedelta | None:
    """Map a configured time_window string to a concrete timedelta."""
    if not time_window:
        return None
    mapping: dict[str, timedelta] = {
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "3d": timedelta(days=3),
        "7d": timedelta(days=7),
    }
    return mapping.get(time_window)


def _filter_by_time_window(documents: list[WebDocument], time_window: str | None) -> list[WebDocument]:
    """Apply a strict client-side cutoff based on published_at timestamps.

    This reinforces the LangSearch freshness hint so that UIs like "Past 6 hours"
    behave more intuitively even if the upstream search provider returns older,
    highly-ranked documents.
    """

    delta = _get_window_timedelta(time_window)
    if not delta:
        return documents

    now = datetime.now(timezone.utc)
    cutoff = now - delta
    filtered = [doc for doc in documents if doc.published_at and doc.published_at >= cutoff]

    # If everything was filtered out (e.g. no truly recent docs), fall back to
    # the original set so the user still sees some signal rather than "no data".
    return filtered or documents


async def fetch_documents(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    documents: list[WebDocument] = []

    if "web" in request.platforms:
        client = LangSearchClient()
        query = _build_query(request)
        logger.info(
            "[snapshot] Fetching LangSearch documents",
            extra={
                "platforms": request.platforms,
                "time_window": request.time_window,
                "focus_areas": request.focus_areas,
                "query": query,
            },
        )
        try:
            documents = await client.search(
                query=query,
                focus_areas=request.focus_areas,
                time_window=request.time_window,
                limit=15,
            )
            documents = _filter_by_time_window(documents, request.time_window)
        except Exception as exc:  # pragma: no cover - network/api failures
            logger.exception("LangSearch fetch failed; continuing with empty result set")
            documents = []
        else:
            logger.info(
                "[snapshot] LangSearch returned %d documents after filtering",
                len(documents),
                extra={"platforms": request.platforms, "time_window": request.time_window},
            )

    state["documents"] = documents
    return state


POSITIVE_HINTS = {"improved", "great", "excellent", "success", "appreciate", "happy", "resolved"}
NEGATIVE_HINTS = {"delay", "problem", "issue", "concern", "warning", "outage", "flood", "traffic", "risk"}


def _score_sentiment(text: str) -> str:
    lowered = text.lower()
    pos_hits = sum(word in lowered for word in POSITIVE_HINTS)
    neg_hits = sum(word in lowered for word in NEGATIVE_HINTS)
    if neg_hits > pos_hits:
        return "negative"
    if pos_hits > neg_hits:
        return "positive"
    return "neutral"


def label_sentiment(state: SnapshotState) -> SnapshotState:
    enriched: list[WebDocument] = []
    for doc in state.get("documents", []):
        sentiment = doc.sentiment or _score_sentiment(doc.snippet)
        enriched.append(doc.model_copy(update={"sentiment": sentiment}))
    state["enriched"] = enriched
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
        for focus in (request.focus_areas or ["Operations"]):
            related = [doc for doc in docs if focus.lower() in (doc.snippet.lower() + doc.title.lower())]
            snippet = related[0].snippet if related else (docs[0].snippet if docs else "Residents request timely advisories.")
            insights.append(
                Insight(
                    category=focus.title(),
                    title=f"Monitor {focus.title()} developments",
                    detail=snippet[:240],
                    evidence=[doc.url for doc in related[:2] if doc.url],
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
graph.add_node("build_snapshot", build_snapshot)

graph.add_edge(START, "fetch_documents")
graph.add_edge("fetch_documents", "label_sentiment")
graph.add_edge("label_sentiment", "build_snapshot")
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
