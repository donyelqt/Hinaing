"""Agent-facing helper functions for insights workflow."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from ...schemas.snapshot import SnapshotRequest, WebDocument
from ...schemas.social import RawSocialPost
from ...schemas.query import QueryPlan
from ..ingestion.facebook import ApifyRunError, fetch_public_posts
from ..ingestion.reddit import fetch_reddit_posts as fetch_reddit_posts_praw, fetch_subreddit_posts
from ..langsearch import LangSearchClient

logger = logging.getLogger(__name__)


def _get_time_search_suffix(time_window: str | None) -> str:
    """Generate search operator suffix for time-based filtering.
    
    Uses Google-style 'after:' operator to prioritize recent content.
    """
    if not time_window:
        return ""
    
    now = datetime.now(timezone.utc)
    
    if time_window == "6h":
        # For 6h, use today's date to get freshest content
        date_str = now.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    elif time_window == "24h":
        # For 24h, use yesterday's date
        yesterday = now - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    elif time_window == "3d":
        cutoff = now - timedelta(days=3)
        date_str = cutoff.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    elif time_window == "7d":
        cutoff = now - timedelta(days=7)
        date_str = cutoff.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    
    return ""

# Baguio-specific location terms for filtering
BAGUIO_LOCATION_TERMS = {
    "baguio", "benguet", "cordillera", "session road", "burnham park",
    "kennon road", "marcos highway", "la trinidad", "panagbenga",
    "camp john hay", "mines view", "wright park", "baguio general hospital",
    "bgh", "summer capital", "city of pines", "governor pack", "abanao",
    "porta vaga", "sm baguio", "baguio city market",
}

# Domains to exclude from search results
EXCLUDED_DOMAINS = {
    "wikipedia.org", "wikimedia.org", "wikidata.org", "britannica.com",
    "dictionary.com", "quora.com", "tripadvisor.com", "booking.com",
    "agoda.com", "expedia.com", "airbnb.com", "pinterest.com",
}

# Focus area concern keywords for query building
# Organized by priority (most searchable terms first), no duplicates across categories
FOCUS_CONCERN_KEYWORDS: dict[str, list[str]] = {
    "infrastructure": [
        "Baguio traffic congestion", "Baguio road repair", "Baguio water shortage",
        "Baguio power outage", "Baguio internet problem", "Kennon Road closure",
        "Session Road rehabilitation", "Baguio parking problem", "Baguio drainage issue",
        "Baguio construction delay", "Baguio jeepney modernization", "Baguio public transport",
    ],
    "health": [
        "Baguio hospital issue", "BGH Baguio problem", "Baguio healthcare concern",
        "Baguio dengue outbreak", "Baguio COVID update", "Baguio mental health",
        "Baguio medical services", "Baguio health center", "Baguio medicine shortage",
        "Baguio doctor shortage", "Baguio emergency room", "Baguio vaccination",
        "BGH substandard construction", "BGH construction issue", "Baguio General Hospital problem",
    ],
    "safety": [
        "Baguio crime incident", "Baguio landslide warning", "Baguio earthquake drill",
        "Baguio fire incident", "Baguio accident report", "Baguio theft problem",
        "Baguio road accident", "Baguio emergency response", "Baguio disaster preparedness",
        "Baguio missing person", "Baguio police operation", "Baguio evacuation",
        "Baguio flood control", "Baguio corruption issue", "Baguio flood control corruption",
        "Baguio students walkout", "Baguio student protest", "Baguio youth rally",
    ],
    "tourism": [
        "Baguio tourist complaint", "Baguio overcrowding", "Burnham Park problem",
        "Baguio hotel issue", "Baguio scam tourist", "Baguio travel advisory",
        "Baguio tourist trap", "Session Road crowd", "Baguio weekend traffic",
        "Baguio accommodation problem", "Baguio tour package complaint", "Panagbenga issue",
    ],
    "economy": [
        "Baguio vendor issue", "Baguio market problem", "Baguio business closure",
        "Baguio mallification protest", "SM Baguio expansion", "Baguio public market",
        "Baguio unemployment", "Baguio cost of living", "Baguio livelihood program",
        "Baguio student protest market", "Baguio vendor displacement", "Baguio job hiring",
    ],
    "environment": [
        "Baguio tree cutting", "Baguio air pollution", "Baguio flooding",
        "Baguio waste management", "Baguio urban development", "Baguio green space",
        "Baguio climate change", "Baguio pine trees", "Baguio environmental concern",
        "Baguio garbage problem", "Baguio illegal dumping", "Baguio water pollution",
    ],
}


def build_focus_query(request: SnapshotRequest) -> str:
    """Construct a search query based on selected focus areas.
    
    Includes time-based search operators (after:YYYY-MM-DD) to prioritize
    recent content based on the requested time_window.
    """
    # Get time suffix for freshness (e.g., " after:2024-12-09")
    time_suffix = _get_time_search_suffix(request.time_window)
    
    if request.focus_areas:
        all_terms: list[str] = []
        for area in request.focus_areas:
            area_lower = area.lower()
            terms = FOCUS_CONCERN_KEYWORDS.get(area_lower)
            if terms:
                all_terms.extend(terms)
            else:
                all_terms.append(f"Baguio {area} problem")
                all_terms.append(f"Baguio {area} concern")
        unique_terms = list(dict.fromkeys(all_terms))
        terms_query = " OR ".join(f'"{term}"' for term in unique_terms[:8])
        base_query = f"({terms_query})"
        logger.info("[build_focus_query] Query with time filter: %s%s", base_query[:80], time_suffix)
        return f"{base_query}{time_suffix}"
    
    base_query = '"Baguio City" AND (problem OR issue OR concern)'
    logger.info("[build_focus_query] Default query with time filter: %s%s", base_query, time_suffix)
    return f"{base_query}{time_suffix}"


def get_window_timedelta(time_window: str | None) -> timedelta | None:
    """Convert time window string to timedelta."""
    if not time_window:
        return None
    mapping = {"6h": timedelta(hours=6), "24h": timedelta(hours=24), "3d": timedelta(days=3), "7d": timedelta(days=7)}
    return mapping.get(time_window)


def filter_by_time_window(documents: list[WebDocument], time_window: str | None) -> list[WebDocument]:
    """Filter documents by time window."""
    delta = get_window_timedelta(time_window)
    if not delta:
        return documents
    now = datetime.now(timezone.utc)
    cutoff = now - delta
    filtered = [doc for doc in documents if doc.published_at and doc.published_at >= cutoff]
    return filtered or documents


def filter_by_location(documents: list[WebDocument]) -> list[WebDocument]:
    """Filter documents to only include Baguio-related content."""
    filtered: list[WebDocument] = []
    for doc in documents:
        url_str = str(doc.url) if doc.url else ""
        searchable = f"{doc.title} {doc.snippet} {url_str}".lower()
        if any(term in searchable for term in BAGUIO_LOCATION_TERMS):
            filtered.append(doc)
        else:
            logger.debug("Filtered out non-Baguio document: %s", doc.title[:50] if doc.title else "Untitled")
    return filtered


def filter_excluded_sources(documents: list[WebDocument]) -> list[WebDocument]:
    """Filter out documents from excluded domains."""
    filtered: list[WebDocument] = []
    for doc in documents:
        url = str(doc.url).lower() if doc.url else ""
        if any(domain in url for domain in EXCLUDED_DOMAINS):
            logger.debug("Filtered out excluded source: %s", doc.url)
            continue
        filtered.append(doc)
    return filtered


def deduplicate_documents(documents: list[WebDocument]) -> list[WebDocument]:
    """Remove duplicate documents based on URL and similar titles."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[WebDocument] = []
    
    for doc in documents:
        # Normalize URL for comparison
        url = str(doc.url).lower().rstrip("/") if doc.url else ""
        
        # Skip if URL already seen
        if url and url in seen_urls:
            logger.debug("Filtered duplicate URL: %s", doc.url)
            continue
        
        # Normalize title for comparison (first 50 chars, lowercase, alphanumeric only)
        title_key = "".join(c for c in (doc.title or "")[:50].lower() if c.isalnum())
        
        # Skip if very similar title already seen
        if title_key and title_key in seen_titles:
            logger.debug("Filtered duplicate title: %s", doc.title[:50] if doc.title else "")
            continue
        
        if url:
            seen_urls.add(url)
        if title_key:
            seen_titles.add(title_key)
        unique.append(doc)
    
    if len(documents) != len(unique):
        logger.info(f"Deduplicated {len(documents)} -> {len(unique)} documents")
    
    return unique


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
    web_docs = deduplicate_documents(web_docs)
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
    docs = deduplicate_documents(docs)
    return docs


# Maximum Reddit documents to return (consistent with LangSearch limit)
MAX_REDDIT_DOCUMENTS = 25


def _map_time_window_to_reddit_filter(time_window: str | None) -> str:
    """Map time window to Reddit's time_filter parameter."""
    if not time_window:
        return "week"
    mapping = {
        "6h": "day",    # Reddit doesn't have 6h, use day
        "24h": "day",
        "3d": "week",   # Reddit doesn't have 3d, use week
        "7d": "week",
    }
    return mapping.get(time_window, "week")


async def fetch_reddit_documents(
    request: SnapshotRequest,
    query_plan: QueryPlan | None = None,
) -> list[WebDocument]:
    """Fetch Reddit posts about Baguio using targeted subreddit searches.
    
    Strategy:
    1. Extract keywords from query_plan (orchestrator output)
    2. Search r/baguio and r/Philippines with those keywords
    3. Apply Baguio location filter to remove irrelevant posts
    4. Deduplicate and cap at MAX_REDDIT_DOCUMENTS
    """
    import re
    
    time_filter = _map_time_window_to_reddit_filter(request.time_window)
    all_docs: list[WebDocument] = []
    focus_areas = request.focus_areas or []
    
    # Target subreddits with Baguio content
    target_subreddits = ["baguio", "Philippines", "CasualPH"]
    
    # Build queries from orchestrator output
    queries_to_run: list[str] = []
    
    # PRIORITY 1: Extract queries from query_plan (orchestrator output)
    if query_plan and query_plan.queries:
        for task in query_plan.queries[:2]:  # Use first 2 query tasks
            # Extract quoted phrases from orchestrator query
            # e.g., ("Baguio mallification" OR "SM Prime Baguio") -> ["Baguio mallification", "SM Prime Baguio"]
            phrases = re.findall(r'"([^"]+)"', task.query)
            for phrase in phrases[:4]:  # Limit phrases per task
                # Clean phrase for Reddit search
                clean_phrase = phrase.strip()
                if clean_phrase and clean_phrase not in queries_to_run:
                    queries_to_run.append(clean_phrase)
        
        logger.info("[reddit_tool] Extracted %d queries from orchestrator: %s", 
                    len(queries_to_run), queries_to_run[:5])
    
    # PRIORITY 2: Fallback to focus-area queries if orchestrator gave nothing useful
    if len(queries_to_run) < 2:
        focus_queries = {
            "economy": ["Baguio market", "Baguio vendor", "SM Baguio", "public market"],
            "safety": ["Baguio crime", "Baguio accident", "Baguio landslide"],
            "health": ["Baguio hospital", "BGH Baguio", "Baguio health"],
            "infrastructure": ["Baguio traffic", "Session Road", "Kennon Road"],
            "tourism": ["Baguio travel", "Burnham Park", "Baguio tourist"],
            "environment": ["Baguio pollution", "Baguio trees", "Baguio environment"],
        }
        
        for area in focus_areas:
            area_lower = area.lower()
            if area_lower in focus_queries:
                for q in focus_queries[area_lower][:2]:
                    if q not in queries_to_run:
                        queries_to_run.append(q)
    
    # Always include base Baguio query as fallback
    if not queries_to_run:
        queries_to_run.append("Baguio")
    
    # Limit total queries to avoid rate limits
    queries_to_run = queries_to_run[:6]
    
    logger.info("[reddit_tool] Running %d queries in %d subreddits: %s", 
                len(queries_to_run), len(target_subreddits), queries_to_run)
    
    # Calculate per-query limit
    per_query_limit = max(10, MAX_REDDIT_DOCUMENTS // max(1, len(queries_to_run)))
    
    # Search targeted subreddits (not Reddit-wide to avoid irrelevant results)
    for query in queries_to_run:
        logger.info("[reddit_tool] Searching subreddits for: %s (limit=%d)", query, per_query_limit)
        
        try:
            docs = await fetch_reddit_posts_praw(
                query=query,
                subreddits=target_subreddits,  # Search specific subreddits
                limit=per_query_limit,
                time_filter=time_filter,
            )
            all_docs.extend(docs)
        except Exception as e:
            logger.warning("[reddit_tool] Query '%s' failed: %s", query, e)
    
    # If no results from subreddits, try Reddit-wide with strict Baguio filter
    if not all_docs:
        logger.info("[reddit_tool] No subreddit results, trying Reddit-wide with Baguio filter")
        
        try:
            docs = await fetch_reddit_posts_praw(
                query="Baguio",
                subreddits=None,  # Reddit-wide
                limit=50,  # Fetch more to filter
                time_filter=time_filter,
            )
            all_docs.extend(docs)
        except Exception as e:
            logger.warning("[reddit_tool] Reddit-wide search failed: %s", e)
    
    # CRITICAL: Filter to only Baguio-related posts
    before_filter = len(all_docs)
    all_docs = filter_by_location(all_docs)
    logger.info("[reddit_tool] Location filter: %d -> %d docs", before_filter, len(all_docs))
    
    # Deduplicate
    all_docs = deduplicate_documents(all_docs)
    
    # Apply time filter if we have enough docs
    if len(all_docs) > 10:
        all_docs = filter_by_time_window(all_docs, request.time_window)
    
    # Rerank by semantic relevance (like LangSearch) before capping
    if len(all_docs) > MAX_REDDIT_DOCUMENTS:
        try:
            rerank_query = f"Baguio {' '.join(focus_areas)}" if focus_areas else "Baguio"
            client = LangSearchClient()
            all_docs = await client.rerank(query=rerank_query, documents=all_docs)
            logger.info("[reddit_tool] Reranked %d docs by relevance", len(all_docs))
        except Exception as e:
            logger.warning("[reddit_tool] Rerank failed, using original order: %s", e)
        
        # Cap at MAX_REDDIT_DOCUMENTS
        logger.info("[reddit_tool] Capping results: %d -> %d", len(all_docs), MAX_REDDIT_DOCUMENTS)
        all_docs = all_docs[:MAX_REDDIT_DOCUMENTS]
    
    logger.info("[reddit_tool] Fetched %d Reddit documents", len(all_docs))
    return all_docs





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
