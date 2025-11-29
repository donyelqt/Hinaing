"""Agent-facing helper functions for insights workflow."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from ...schemas.snapshot import SnapshotRequest, WebDocument
from ...schemas.social import RawSocialPost
from ..ingestion.facebook import ApifyRunError, fetch_public_posts
from ..ingestion.reddit import fetch_public_posts as fetch_reddit_posts
from ..langsearch import LangSearchClient
from .tools import (
    build_focus_query,
    filter_by_location,
    filter_by_time_window,
    filter_excluded_sources,
)

logger = logging.getLogger(__name__)


def _facebook_post_to_webdoc(post: RawSocialPost) -> WebDocument:
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


def _domain_from_url(doc: WebDocument) -> str:
    if not doc.url:
        return "unknown"
    parsed = urlparse(str(doc.url))
    return parsed.netloc or "unknown"


async def search_web_documents(
    request: SnapshotRequest,
    *,
    limit: int = 25,
    custom_query: str | None = None,
) -> list[WebDocument]:
    """Call LangSearch using the focus-aware query."""
    client = LangSearchClient()
    query = custom_query or build_focus_query(request)
    web_docs = await client.search(
        query=query,
        focus_areas=request.focus_areas,
        time_window=request.time_window,
        limit=limit,
    )
    web_docs = filter_excluded_sources(web_docs)
    web_docs = filter_by_location(web_docs)
    web_docs = filter_by_time_window(web_docs, request.time_window)
    return web_docs


async def fetch_facebook_documents(request: SnapshotRequest) -> list[WebDocument]:
    """Fetch Facebook group posts via Apify and convert to WebDocument."""
    try:
        posts = await fetch_public_posts(region_keywords=request.focus_areas)
    except ApifyRunError as exc:
        logger.error("Apify Facebook scraper failed: %s", exc)
        return []
    docs = [_facebook_post_to_webdoc(post) for post in posts]
    docs = filter_by_location(docs)
    docs = filter_by_time_window(docs, request.time_window)
    return docs


def assign_sentiment(documents: list[WebDocument]) -> list[WebDocument]:
    """Fallback sentiment assignment using simple heuristics.
    
    Note: Primary sentiment analysis uses HybridSentimentAgent (RoBERTa + Gemini).
    This function is only called as a last-resort fallback.
    """
    positive_hints = {"improved", "great", "excellent", "success", "appreciate", "happy", "resolved", "good"}
    negative_hints = {"delay", "problem", "issue", "concern", "warning", "outage", "flood", "traffic", "risk", "accident", "crime"}
    
    enriched: list[WebDocument] = []
    for doc in documents:
        if doc.sentiment:
            enriched.append(doc)
            continue
        
        text = f"{doc.title} {doc.snippet}".lower()
        pos_hits = sum(word in text for word in positive_hints)
        neg_hits = sum(word in text for word in negative_hints)
        
        if neg_hits > pos_hits:
            sentiment = "negative"
        elif pos_hits > neg_hits:
            sentiment = "positive"
        else:
            sentiment = "neutral"
        
        enriched.append(doc.model_copy(update={"sentiment": sentiment}))
    return enriched


def score_credibility(documents: list[WebDocument]) -> dict[str, float]:
    """Compute lightweight credibility ratios per domain."""
    notes: dict[str, float] = {}
    for doc in documents:
        domain = _domain_from_url(doc)
        score = 1.0
        if domain == "unknown":
            score -= 0.2
        elif domain.endswith(".gov.ph") or domain.endswith(".org"):
            score += 0.2
        if doc.published_at:
            age_hours = (datetime.now(timezone.utc) - doc.published_at).total_seconds() / 3600
            if age_hours > 48:
                score -= 0.2
        notes[domain] = max(0.1, min(1.5, score))
    return notes


THEME_GROUPS: dict[str, dict[str, Any]] | None = None


def set_theme_groups(theme_groups: dict[str, dict[str, Any]]) -> None:
    """Allow graph to pass the theme configuration for routing calls."""
    global THEME_GROUPS
    THEME_GROUPS = theme_groups


def route_documents_by_theme(
    documents: list[WebDocument],
    focus_areas: list[str] | None,
) -> dict[str, list[WebDocument]]:
    """Cluster documents per configured theme."""
    if THEME_GROUPS is None:
        raise RuntimeError("Theme groups not configured for agent tools")

    focus_values = {focus.lower() for focus in (focus_areas or [])}
    theme_docs: dict[str, list[WebDocument]] = {key: [] for key in THEME_GROUPS}

    for doc in documents:
        content = f"{doc.title} {doc.snippet}".lower()
        for key, meta in THEME_GROUPS.items():
            focus_match = bool(focus_values & set(meta.get("focus_values", set())))
            keyword_match = any(word in content for word in meta.get("keywords", set()))
            if focus_match or keyword_match:
                theme_docs[key].append(doc)
    
    # Log routing stats for debugging
    stats = {k: len(v) for k, v in theme_docs.items()}
    logger.info("[theme_router] Routing stats: %s", stats)
    
    return theme_docs
