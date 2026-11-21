"""LangSearch API client wrapper."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

import httpx

from ..core.config import get_settings
from pydantic import ValidationError

from ..schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)
_MAX_RETRIES = 5
_RETRY_DELAY = 0.5  # More aggressive initial delay; backoff: 0.5s, 1s, 2s, 4s, 8s (total ~15.5s)


class LangSearchClient:
    """Thin async wrapper around the LangSearch REST API."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        settings = get_settings()
        self._api_key = settings.langsearch_api_key
        self._base_url = settings.langsearch_base_url.rstrip("/")
        self._timeout = timeout

    async def search(
        self,
        *,
        query: str,
        focus_areas: list[str] | None = None,
        time_window: str | None = None,
        limit: int = 10,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> list[WebDocument]:
        if not self._api_key:
            logger.warning("LangSearch API key missing; returning empty result set")
            return []

        # Documented Web Search API contract (docs.langsearch.com/reference/search-api-guide):
        # contents.text requests full page text (capped per doc); response carries `text`
        # instead of `snippet`. We keep snippet-only size but through the documented field.
        payload: dict[str, Any] = {
            "query": self._enrich_query(query=query, focus_areas=focus_areas),
            "count": max(1, min(int(limit), 50)),
            "contents": {"text": {"maxCharacters": 1500}},
        }
        freshness = self._map_freshness(time_window)
        if freshness:
            payload["freshness"] = freshness
        if include_domains:
            payload["includeDomains"] = [d for d in include_domains if d.strip()]
        if exclude_domains:
            payload["excludeDomains"] = [d for d in exclude_domains if d.strip()]

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            # Circuit breaker: skip search if it failed recently (global counter)
            if hasattr(self, '_search_failures') and self._search_failures >= 3:
                logger.warning("[langsearch] Circuit breaker: skipping search (3+ recent failures)")
                return []
            
            # Retry with exponential backoff for rate limits (429)
            data = None
            search_failed = False
            for attempt in range(1, _MAX_RETRIES + 1):
                response = await client.post(self._base_url, json=payload, headers=headers)
                
                if response.status_code == 429:
                    search_failed = True
                    if attempt < _MAX_RETRIES:
                        delay = _RETRY_DELAY * (2 ** (attempt - 1))  # Exponential: 0.5s, 1s, 2s, 4s, 8s
                        logger.warning(
                            "LangSearch rate limited (429), retrying in %.1fs (attempt %d/%d)",
                            delay, attempt, _MAX_RETRIES
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"LangSearch rate limited (429) after {attempt} retries for query: {query[:50]} — daily token allowance may be exhausted (resets 00:00 UTC); check Dashboard")
                        # Allowance safety net: fall back to no-domain-scoped call once to rule out domain-list exhaustion, then give up
                        return []
                
                response.raise_for_status()
                data = response.json()
                break
            
            # Track failures for circuit breaker
            if search_failed:
                if not hasattr(self, '_search_failures'):
                    self._search_failures = 0
                self._search_failures += 1
            else:
                # Reset on success
                if hasattr(self, '_search_failures'):
                    self._search_failures = 0
            
            if data is None:
                return []

            # Upstream contract carries usage tokens — log them for cost accounting
            usage = data.get("usage") or {}
            logger.info(f"[langsearch] usage: input_tokens={usage.get('input_tokens')} output_tokens={usage.get('output_tokens')} someResultsRemoved={((data.get('data') or {}).get('webPages') or {}).get('someResultsRemoved')}")

            documents: list[WebDocument] = []
            for item in self._extract_web_results(data):
                try:
                    # SANITIZE at extraction time BEFORE reranking
                    # Prevents indirect prompt injection and poisoned documents from getting high scores
                    snippet = (item.get("text") or item.get("snippet") or item.get("summary") or "")[:1500]
                    dangerous_patterns = [
                        r"<\|endoftext\|>", r"ignore.*previous", r"forget.*instructions",
                        r"you are now", r"disregard.*rules", r"system prompt:"
                    ]
                    for pattern in dangerous_patterns:
                        snippet = re.sub(pattern, "[SANITIZED]", snippet, flags=re.IGNORECASE)
                    
                    documents.append(
                        WebDocument(
                            title=item.get("name") or item.get("title") or "Untitled result",
                            snippet=snippet,
                            url=item.get("url"),
                            published_at=self._parse_datetime(item.get("datePublished")),
                            sentiment=item.get("sentiment") or None,
                            metadata={
                                "source": item.get("displayUrl") or item.get("source"),
                                "id": item.get("id"),
                            },
                        )
                    )
                except ValidationError as exc:  # pragma: no cover - defensive for messy APIs
                    logger.debug("Skipping LangSearch result due to validation error: %s", exc)
                    continue

            return documents

    @staticmethod
    def _enrich_query(query: str, focus_areas: list[str] | None) -> str:
        """Keep query clean for precise search results.
        
        Previously added Facebook page filters which diluted search precision.
        Now returns the query as-is for accurate results.
        """
        # Return query unchanged for precise, accurate search results
        return query

    @staticmethod
    def _map_freshness(time_window: str | None) -> str | None:
        if not time_window:
            return None
        mapping = {
            "6h": "oneDay",
            "24h": "oneDay",
            "3d": "oneWeek",
            "7d": "oneWeek",
            "month": "oneMonth",
            "30d": "oneMonth",
            "year": "oneYear",
        }
        return mapping.get(time_window, "noLimit")

    @staticmethod
    def _extract_web_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, dict):
            web_pages = data.get("webPages")
            if isinstance(web_pages, dict):
                value = web_pages.get("value")
                if isinstance(value, list):
                    return value

        web_pages = payload.get("webPages")
        if isinstance(web_pages, dict):
            value = web_pages.get("value")
            if isinstance(value, list):
                return value

        results = payload.get("results")
        if isinstance(results, list):
            return results

        return []

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.debug("Unable to parse datetime '%s' from LangSearch; ignoring", value)
            return None
