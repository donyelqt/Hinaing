"""Facebook ingestion via Apify Facebook Groups Scraper.

Uses async run pattern for production-grade scraping:
1. Start actor run
2. Poll until completion
3. Fetch dataset items
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Iterable

import httpx

from ...core.config import get_settings
from ...schemas.social import LocationContext, RawSocialPost, SourcePlatform

logger = logging.getLogger(__name__)

# Apify API base URL
APIFY_BASE_URL = "https://api.apify.com/v2"

# Polling configuration
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 120  # 10 minutes max wait


class ApifyRunError(Exception):
    """Raised when Apify actor run fails."""
    pass


async def fetch_public_posts(region_keywords: Iterable[str] | None = None) -> list[RawSocialPost]:
    """Fetch posts from Facebook groups via Apify scraper.
    
    Args:
        region_keywords: Optional keywords to filter posts (used as search query).
        
    Returns:
        List of RawSocialPost objects from the scraped Facebook groups.
        
    Raises:
        ApifyRunError: If the actor run fails or times out.
        httpx.HTTPStatusError: If API requests fail.
    """
    settings = get_settings()
    
    if not settings.apify_api_token:
        raise ApifyRunError("APIFY_API_TOKEN not configured")
    
    group_urls = json.loads(settings.apify_facebook_group_urls)
    if not group_urls:
        logger.warning("No Facebook group URLs configured")
        return []
    
    search_query = " ".join(region_keywords) if region_keywords else ""
    
    payload = {
        "startUrls": [{"url": url} for url in group_urls],
        "resultsLimit": settings.apify_facebook_results_limit,
        "sortBy": "new",
    }
    
    if search_query:
        payload["searchQuery"] = search_query

    actor_run_url = f"{APIFY_BASE_URL}/acts/{settings.apify_facebook_groups_actor_id}/runs"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Start the actor run
        run_id = await _start_actor_run(client, payload, actor_run_url, settings.apify_api_token)
        logger.info(f"Started Apify run: {run_id}")
        
        # Step 2: Poll until completion
        dataset_id = await _poll_run_status(client, run_id, settings.apify_api_token)
        logger.info(f"Run completed, dataset: {dataset_id}")
        
        # Step 3: Fetch dataset items
        items = await _fetch_dataset_items(client, dataset_id, settings.apify_api_token)
        logger.info(f"Fetched {len(items)} posts from Facebook groups")

    return [_map_to_raw_post(item) for item in items]


async def _start_actor_run(
    client: httpx.AsyncClient, payload: dict[str, Any], actor_run_url: str, api_token: str
) -> str:
    """Start an Apify actor run and return the run ID."""
    response = await client.post(
        actor_run_url,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    response.raise_for_status()
    data = response.json()["data"]
    return data["id"]


async def _poll_run_status(client: httpx.AsyncClient, run_id: str, api_token: str) -> str:
    """Poll the actor run status until completion. Returns dataset ID."""
    run_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
    
    for attempt in range(MAX_POLL_ATTEMPTS):
        response = await client.get(
            run_url,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        response.raise_for_status()
        
        data = response.json()["data"]
        status = data["status"]
        
        if status == "SUCCEEDED":
            return data["defaultDatasetId"]
        
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise ApifyRunError(f"Actor run {run_id} ended with status: {status}")
        
        # Still running, wait and retry
        logger.debug(f"Run {run_id} status: {status}, attempt {attempt + 1}/{MAX_POLL_ATTEMPTS}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
    
    raise ApifyRunError(f"Actor run {run_id} timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s")



async def _fetch_dataset_items(
    client: httpx.AsyncClient, dataset_id: str, api_token: str
) -> list[dict[str, Any]]:
    """Fetch all items from an Apify dataset."""
    dataset_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
    
    response = await client.get(
        dataset_url,
        headers={"Authorization": f"Bearer {api_token}"},
        params={"format": "json"},
    )
    response.raise_for_status()
    return response.json()


def _map_to_raw_post(item: dict[str, Any]) -> RawSocialPost:
    """Map Apify Facebook Groups Scraper output to RawSocialPost schema."""
    return RawSocialPost(
        platform=SourcePlatform(
            name="facebook",
            identifier=item.get("groupUrl", "unknown-group"),
        ),
        post_id=item.get("postId", item.get("id", "")),
        author=item.get("authorName", item.get("user", {}).get("name", "Unknown")),
        content=item.get("text", item.get("message", "")),
        url=item.get("postUrl", item.get("url")),
        created_at=_parse_timestamp(item.get("timestamp", item.get("time"))),
        location=LocationContext(),
        metadata={
            "likes": item.get("likesCount", item.get("likes", 0)),
            "comments_count": item.get("commentsCount", item.get("comments", 0)),
            "shares": item.get("sharesCount", item.get("shares", 0)),
            "comments_data": item.get("comments", []) if isinstance(item.get("comments"), list) else [],
            "group_name": item.get("groupName", ""),
            "media": item.get("media", []),
            "author_url": item.get("authorUrl", item.get("user", {}).get("url", "")),
        },
    )


def _parse_timestamp(ts: str | None) -> datetime:
    """Parse timestamp from Apify output."""
    if not ts:
        return datetime.utcnow()
    
    try:
        # Handle ISO format with Z suffix
        if isinstance(ts, str):
            ts = ts.replace("Z", "+00:00")
            return datetime.fromisoformat(ts)
    except ValueError:
        pass
    
    # Fallback to current time
    return datetime.utcnow()
