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
from ..ingestion.facebook import ApifyRunError, fetch_public_posts
from ...schemas.social import RawSocialPost
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
    # Concern/problem keywords - strict focus on issues only
    concern_modifiers = ["problem", "issue", "concern", "complaint", "crisis"]
    
    # Map focus areas to Baguio-specific concern terms
    # Each theme has problem-focused search terms
    focus_concern_keywords: dict[str, list[str]] = {
        "infrastructure": [
            "Baguio road problem",
            "Baguio traffic issue",
            "Baguio water problem",
            "Baguio power outage",
            "Baguio pothole complaint",
            "Kennon Road problem",
            "Baguio jeepney concern",
            "Baguio garbage issue",
            "Session Road traffic",
        ],
        "health": [
            "Baguio hospital problem",
            "Baguio health concern",
            "Baguio disease issue",
            "Baguio sanitation problem",
            "Baguio medical complaint",
        ],
        "safety": [
            "Baguio crime problem",
            "Baguio flood concern",
            "Baguio landslide issue",
            "Baguio fire problem",
            "Baguio accident concern",
            "Baguio safety issue",
        ],
        "tourism": [
            "Baguio tourist complaint",
            "Baguio overcrowding problem",
            "Burnham Park issue",
            "Baguio hotel complaint",
            "Baguio tourism concern",
        ],
        "economy": [
            "Baguio vendor problem",
            "Baguio market issue",
            "Baguio business concern",
            "Baguio livelihood problem",
            "Baguio employment issue",
            "Baguio market mallification",
            "Baguio public market mallification",
            "Baguio mallification protest",
            "Baguio public market redevelopment",
            "Baguio PPP market redevelopment",
            "SM Prime Baguio market",
            "Baguio vendor displacement",
        ],
        "environment": [
            "Baguio pollution problem",
            "Baguio air quality concern",
            "Baguio waste issue",
            "Baguio flooding problem",
            "Baguio environmental concern",
        ],
    }

    # Build query - supports multiple selected themes
    if request.focus_areas and len(request.focus_areas) > 0:
        # Collect terms from ALL selected themes
        all_terms: list[str] = []
        for area in request.focus_areas:
            area_lower = area.lower()
            terms = focus_concern_keywords.get(area_lower)
            if terms:
                all_terms.extend(terms)
            else:
                # Fallback for unknown themes
                all_terms.append(f"Baguio {area} problem")
                all_terms.append(f"Baguio {area} concern")

        # De-duplicate while preserving order
        unique_terms = list(dict.fromkeys(all_terms))
        
        # Build OR query for all concern terms
        terms_query = " OR ".join(f'"{term}"' for term in unique_terms)
        query = f'({terms_query})'
    else:
        # Default: general Baguio concerns and problems
        concern_terms = " OR ".join(concern_modifiers)
        query = f'"Baguio City" AND ({concern_terms})'
    
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


# Baguio/Benguet/Cordillera location identifiers for strict filtering
_BAGUIO_LOCATION_TERMS = {
    "baguio",
    "benguet",
    "cordillera",
    "session road",
    "burnham park",
    "kennon road",
    "marcos highway",
    "la trinidad",
    "panagbenga",
    "camp john hay",
    "mines view",
    "wright park",
    "baguio general hospital",
    "bgh",
    "summer capital",
    "city of pines",
    "governor pack",
    "abanao",
    "porta vaga",
}


def _filter_by_location(documents: list[WebDocument]) -> list[WebDocument]:
    """Filter documents to only include those mentioning Baguio/Benguet/Cordillera.
    
    This is a strict post-fetch filter to exclude results from other regions
    (e.g., Metro Manila, Batangas) that may have matched generic keywords.
    """
    filtered: list[WebDocument] = []
    
    for doc in documents:
        # Combine title, snippet, and URL for location matching
        url_str = str(doc.url) if doc.url else ""
        searchable = f"{doc.title} {doc.snippet} {url_str}".lower()
        
        # Check if any Baguio location term appears in the document
        if any(term in searchable for term in _BAGUIO_LOCATION_TERMS):
            filtered.append(doc)
        else:
            logger.debug(
                "Filtered out non-Baguio document: %s",
                doc.title[:50] if doc.title else "Untitled",
            )
    
    # If all documents were filtered out, return empty list
    # (better to show "no data" than irrelevant data)
    return filtered


# Excluded domains - reference sites, not news/concerns sources
_EXCLUDED_DOMAINS = {
    "wikipedia.org",
    "wikimedia.org",
    "wikidata.org",
    "britannica.com",
    "dictionary.com",
    "quora.com",
    "tripadvisor.com",
    "booking.com",
    "agoda.com",
    "expedia.com",
    "airbnb.com",
    "pinterest.com",
}


def _filter_excluded_sources(documents: list[WebDocument]) -> list[WebDocument]:
    """Filter out non-news sources like Wikipedia, travel sites, etc."""
    filtered: list[WebDocument] = []
    for doc in documents:
        url = str(doc.url).lower() if doc.url else ""
        is_excluded = any(domain in url for domain in _EXCLUDED_DOMAINS)
        if not is_excluded:
            filtered.append(doc)
        else:
            logger.debug("Filtered out excluded source: %s", doc.url)
    return filtered


def _facebook_post_to_webdoc(post: RawSocialPost) -> WebDocument:
    """Convert a RawSocialPost from Facebook to WebDocument format."""
    return WebDocument(
        title=f"Facebook: {post.author}",
        snippet=post.content[:500] if post.content else "",
        url=post.url,
        published_at=post.created_at,
        sentiment=None,
        metadata={
            "source": "facebook",
            "post_id": post.post_id,
            "author": post.author,
            "likes": post.metadata.get("likes", 0),
            "comments_count": post.metadata.get("comments_count", 0),
            "group_name": post.metadata.get("group_name", ""),
        },
    )


async def fetch_documents(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    documents: list[WebDocument] = []

    # Fetch from LangSearch (web)
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
            web_docs = await client.search(
                query=query,
                focus_areas=request.focus_areas,
                time_window=request.time_window,
                limit=25,
            )
            web_docs = _filter_excluded_sources(web_docs)
            web_docs = _filter_by_location(web_docs)
            web_docs = _filter_by_time_window(web_docs, request.time_window)
            documents.extend(web_docs)
            logger.info(
                "[snapshot] LangSearch returned %d relevant documents",
                len(web_docs),
            )
        except Exception as exc:
            logger.exception("LangSearch fetch failed; continuing")

    # Fetch from Facebook Groups via Apify
    if "facebook" in request.platforms:
        logger.info("[snapshot] Fetching Facebook group posts via Apify")
        try:
            fb_posts = await fetch_public_posts(region_keywords=request.focus_areas)
            fb_docs = [_facebook_post_to_webdoc(post) for post in fb_posts]
            # Apply Baguio location filter to Facebook posts too
            fb_docs = _filter_by_location(fb_docs)
            fb_docs = _filter_by_time_window(fb_docs, request.time_window)
            documents.extend(fb_docs)
            logger.info(
                "[snapshot] Facebook returned %d relevant posts",
                len(fb_docs),
            )
        except ApifyRunError as exc:
            logger.error("Apify Facebook scraper failed: %s", exc)
        except Exception as exc:
            logger.exception("Facebook fetch failed; continuing")

    # Apply semantic reranking when:
    # - Facebook only: rerank FB posts
    # - Both web + facebook: rerank combined set (web already reranked internally, but need to merge rankings)
    # - Web only: skip (already reranked inside LangSearchClient.search())
    needs_rerank = (
        "facebook" in request.platforms and len(documents) > 1
    )
    
    if needs_rerank:
        query = _build_query(request)
        logger.info("[snapshot] Applying semantic rerank to %d documents", len(documents))
        try:
            reranker = LangSearchClient()
            documents = await reranker.rerank(query=query, documents=documents)
            logger.info("[snapshot] Semantic rerank completed")
        except Exception as exc:
            logger.warning("Semantic rerank failed, using original order: %s", exc)

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
