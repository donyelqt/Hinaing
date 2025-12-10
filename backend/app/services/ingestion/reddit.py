"""Reddit ingestion with JSON endpoint fallback.

Supports two methods:
1. PRAW (official API) - requires Reddit API credentials
2. JSON endpoints (fallback) - no auth needed, rate limited

For academic research on public Reddit data.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Iterable

import httpx

from ...core.config import get_settings
from ...schemas.social import LocationContext, RawSocialPost, SourcePlatform
from ...schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)

# Baguio-related subreddits
BAGUIO_SUBREDDITS = [
    "Baguio",
    "Philippines",
    "CasualPH",
]

# Keywords to filter relevant posts
BAGUIO_KEYWORDS = [
    "baguio", "session road", "burnham", "cordillera",
    "benguet", "la trinidad", "city of pines", "kennon",
]

# Rate limiting for JSON endpoints
_last_request_time = 0.0
_MIN_REQUEST_INTERVAL = 2.0  # 2 seconds between requests


async def _rate_limit():
    """Enforce rate limiting for JSON endpoints."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        await asyncio.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _get_praw_client():
    """Try to initialize PRAW client if valid credentials available."""
    settings = get_settings()
    
    client_id = settings.reddit_client_id
    client_secret = settings.reddit_client_secret
    
    # Check for missing or placeholder credentials
    if not client_id or not client_secret:
        return None
    
    # Detect placeholder values (e.g., "...", "your_id_here", etc.)
    placeholders = ["...", "xxx", "your", "placeholder", "changeme", "none"]
    if any(p in client_id.lower() for p in placeholders) or any(p in client_secret.lower() for p in placeholders):
        logger.info("[reddit] Placeholder credentials detected, skipping PRAW")
        return None
    
    # Credentials look real, but might still be invalid - let caller handle 401
    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=settings.reddit_user_agent,
        )
        logger.info("[reddit] PRAW client initialized")
        return reddit
    except Exception as e:
        logger.warning(f"[reddit] PRAW init failed: {e}")
        return None


def is_baguio_related(text: str, keywords: list[str] | None = None) -> bool:
    """Check if text contains Baguio-related keywords."""
    if not text:
        return False
    text_lower = text.lower()
    check_keywords = keywords or BAGUIO_KEYWORDS
    return any(kw.lower() in text_lower for kw in check_keywords)


async def fetch_reddit_posts(
    query: str,
    subreddits: list[str] | None = None,
    limit: int = 25,
    time_filter: str = "week",
) -> list[WebDocument]:
    """Fetch Reddit posts - uses PRAW if available and working, else JSON fallback."""
    
    # Try PRAW first
    praw_client = _get_praw_client()
    if praw_client:
        results = await _fetch_with_praw(praw_client, query, subreddits, limit, time_filter)
        # If PRAW returned results, use them
        if results:
            return results
        # If PRAW failed (401, etc.), fall through to JSON
        logger.info("[reddit] PRAW returned no results, trying JSON fallback")
    
    # Fallback to JSON endpoints
    logger.info("[reddit] Using JSON endpoint fallback")
    return await _fetch_with_json(query, subreddits, limit, time_filter)


async def _fetch_with_praw(
    reddit,
    query: str,
    subreddits: list[str] | None,
    limit: int,
    time_filter: str,
) -> list[WebDocument]:
    """Fetch using official PRAW API."""
    target_subreddits = subreddits or BAGUIO_SUBREDDITS
    documents = []
    
    try:
        for subreddit_name in target_subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                search_results = subreddit.search(
                    query,
                    sort="relevance",
                    time_filter=time_filter,
                    limit=limit,
                )
                
                for submission in search_results:
                    doc = _praw_submission_to_document(submission)
                    if doc:
                        documents.append(doc)
                        
                logger.info(f"[reddit/praw] Fetched from r/{subreddit_name}")
                
            except Exception as e:
                logger.warning(f"[reddit/praw] Error r/{subreddit_name}: {e}")
                continue
        
        return documents
        
    except Exception as e:
        logger.error(f"[reddit/praw] Search error: {e}")
        return []


async def _fetch_with_json(
    query: str,
    subreddits: list[str] | None,
    limit: int,
    time_filter: str,
) -> list[WebDocument]:
    """Fetch using public JSON endpoints (no auth required).
    
    If subreddits is None or empty, searches ALL of Reddit.
    """
    documents = []
    
    # Map time_filter to Reddit's t parameter
    time_map = {
        "hour": "hour",
        "day": "day",
        "week": "week",
        "month": "month",
        "year": "year",
        "all": "all",
    }
    t_param = time_map.get(time_filter, "week")
    
    headers = {
        "User-Agent": "Hinaing/1.0 (Academic Research; Baguio Sentiment Analysis)"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # If no subreddits specified, search ALL of Reddit
        if not subreddits:
            await _rate_limit()
            
            # Reddit-wide search (no restrict_sr)
            url = "https://www.reddit.com/search.json"
            params = {
                "q": query,
                "sort": "relevance",
                "t": t_param,
                "limit": min(limit, 100),
            }
            
            try:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 429:
                    logger.warning("[reddit/json] Rate limited, waiting 60s...")
                    await asyncio.sleep(60)
                elif response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    
                    for child in children:
                        post = child.get("data", {})
                        doc = _json_post_to_document(post, "all")
                        if doc:
                            documents.append(doc)
                    
                    logger.info(f"[reddit/json] Reddit-wide search: {len(children)} raw, {len(documents)} converted")
                else:
                    logger.warning(f"[reddit/json] HTTP {response.status_code} for Reddit-wide search")
            except Exception as e:
                logger.warning(f"[reddit/json] Error in Reddit-wide search: {e}")
        else:
            # Search specific subreddits
            for subreddit_name in subreddits:
                try:
                    await _rate_limit()
                    
                    url = f"https://www.reddit.com/r/{subreddit_name}/search.json"
                    params = {
                        "q": query,
                        "restrict_sr": "1",
                        "sort": "relevance",
                        "t": t_param,
                        "limit": min(limit, 100),
                    }
                    
                    response = await client.get(url, headers=headers, params=params)
                    
                    if response.status_code == 429:
                        logger.warning("[reddit/json] Rate limited, waiting 60s...")
                        await asyncio.sleep(60)
                        continue
                    
                    if response.status_code != 200:
                        logger.warning(f"[reddit/json] HTTP {response.status_code} for r/{subreddit_name}")
                        continue
                    
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    
                    converted = 0
                    for child in children:
                        post = child.get("data", {})
                        doc = _json_post_to_document(post, subreddit_name)
                        if doc:
                            documents.append(doc)
                            converted += 1
                    
                    logger.info(f"[reddit/json] r/{subreddit_name}: {len(children)} raw, {converted} converted")
                    
                except Exception as e:
                    logger.warning(f"[reddit/json] Error r/{subreddit_name}: {e}")
                    continue
    
    logger.info(f"[reddit/json] Total: {len(documents)} posts")
    return documents


async def fetch_subreddit_posts(
    subreddit_name: str = "Baguio",
    sort: str = "new",
    limit: int = 50,
    keywords: list[str] | None = None,
) -> list[WebDocument]:
    """Fetch recent posts from a specific subreddit."""
    
    # Try PRAW first
    praw_client = _get_praw_client()
    if praw_client:
        results = await _fetch_subreddit_praw(praw_client, subreddit_name, sort, limit, keywords)
        if results:
            return results
        logger.info("[reddit] PRAW returned no results, trying JSON fallback")
    
    # JSON fallback
    return await _fetch_subreddit_json(subreddit_name, sort, limit, keywords)


async def _fetch_subreddit_praw(reddit, subreddit_name: str, sort: str, limit: int, keywords: list[str] | None) -> list[WebDocument]:
    """Fetch subreddit posts using PRAW."""
    documents = []
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        if sort == "hot":
            posts = subreddit.hot(limit=limit)
        elif sort == "new":
            posts = subreddit.new(limit=limit)
        elif sort == "top":
            posts = subreddit.top(limit=limit, time_filter="week")
        elif sort == "rising":
            posts = subreddit.rising(limit=limit)
        else:
            posts = subreddit.new(limit=limit)
        
        for submission in posts:
            if keywords:
                text = f"{submission.title} {submission.selftext}"
                if not is_baguio_related(text, keywords):
                    continue
            
            doc = _praw_submission_to_document(submission)
            if doc:
                documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"[reddit/praw] Error r/{subreddit_name}: {e}")
        return []


async def _fetch_subreddit_json(subreddit_name: str, sort: str, limit: int, keywords: list[str] | None) -> list[WebDocument]:
    """Fetch subreddit posts using JSON endpoint."""
    documents = []
    
    headers = {
        "User-Agent": "Hinaing/1.0 (Academic Research; Baguio Sentiment Analysis)"
    }
    
    try:
        await _rate_limit()
        
        url = f"https://www.reddit.com/r/{subreddit_name}/{sort}.json"
        params = {"limit": min(limit, 100)}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.warning(f"[reddit/json] HTTP {response.status_code}")
                return []
            
            data = response.json()
            children = data.get("data", {}).get("children", [])
            
            filtered = 0
            for child in children:
                post = child.get("data", {})
                
                if keywords:
                    text = f"{post.get('title', '')} {post.get('selftext', '')}"
                    if not is_baguio_related(text, keywords):
                        filtered += 1
                        continue
                
                doc = _json_post_to_document(post, subreddit_name)
                if doc:
                    documents.append(doc)
        
        logger.info(f"[reddit/json] r/{subreddit_name}: {len(children)} raw, {filtered} filtered, {len(documents)} final")
        return documents
        
    except Exception as e:
        logger.error(f"[reddit/json] Error: {e}")
        return []


def _praw_submission_to_document(submission) -> WebDocument | None:
    """Convert PRAW Submission to WebDocument."""
    try:
        created_utc = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
        
        content = submission.title
        if submission.selftext and submission.selftext != "[removed]":
            content += f"\n\n{submission.selftext}"
        
        snippet = content[:500] if len(content) > 500 else content
        
        return WebDocument(
            url=f"https://reddit.com{submission.permalink}",
            title=submission.title,
            snippet=snippet,
            published_at=created_utc,
            source="reddit",
            metadata={
                "platform": "reddit",
                "subreddit": submission.subreddit.display_name,
                "author": str(submission.author) if submission.author else "[deleted]",
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "is_self": submission.is_self,
                "flair": submission.link_flair_text,
                "post_id": submission.id,
            },
        )
    except Exception as e:
        logger.warning(f"[reddit/praw] Conversion error: {e}")
        return None


def _json_post_to_document(post: dict, subreddit_name: str) -> WebDocument | None:
    """Convert JSON post data to WebDocument."""
    try:
        # Skip removed/deleted posts
        selftext = post.get("selftext", "")
        if post.get("removed_by_category") or selftext == "[removed]":
            logger.debug(f"[reddit/json] Skipping removed post: {post.get('title', '')[:50]}")
            return None
        
        # Skip if no created_utc (invalid post)
        if not post.get("created_utc"):
            return None
        
        created_utc = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
        
        title = post.get("title", "")
        selftext = post.get("selftext", "")
        
        content = title
        if selftext and selftext != "[removed]" and selftext != "[deleted]":
            content += f"\n\n{selftext}"
        
        snippet = content[:500] if len(content) > 500 else content
        
        permalink = post.get("permalink", "")
        url = f"https://reddit.com{permalink}" if permalink else ""
        
        return WebDocument(
            url=url,
            title=title,
            snippet=snippet,
            published_at=created_utc,
            source="reddit",
            metadata={
                "platform": "reddit",
                "subreddit": post.get("subreddit", subreddit_name),
                "author": post.get("author", "[deleted]"),
                "score": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio", 0),
                "num_comments": post.get("num_comments", 0),
                "is_self": post.get("is_self", True),
                "flair": post.get("link_flair_text"),
                "post_id": post.get("id", ""),
            },
        )
    except Exception as e:
        logger.warning(f"[reddit/json] Conversion error: {e}")
        return None


# Legacy function for backward compatibility
async def fetch_public_posts(region_keywords: Iterable[str]) -> list[RawSocialPost]:
    """Fetch Reddit posts matching the provided keywords."""
    keywords = list(region_keywords)
    query = " OR ".join(keywords[:3])
    
    documents = await fetch_reddit_posts(query, limit=25)
    
    posts = []
    for doc in documents:
        meta = doc.metadata or {}
        posts.append(RawSocialPost(
            platform=SourcePlatform(
                name="reddit",
                identifier=f"r/{meta.get('subreddit', 'unknown')}",
            ),
            post_id=meta.get("post_id", ""),
            author=meta.get("author", "unknown"),
            content=doc.snippet or "",
            created_at=doc.published_at or datetime.now(timezone.utc),
            url=doc.url,
            location=LocationContext(),
            metadata={
                "keywords": keywords,
                "score": meta.get("score", 0),
                "num_comments": meta.get("num_comments", 0),
            },
        ))
    
    return posts
