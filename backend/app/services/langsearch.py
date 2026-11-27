"""LangSearch API client wrapper."""

from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime
from typing import Any

import httpx

from ..core.config import get_settings
from pydantic import ValidationError

from ..schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)
_MAX_RETRIES = 2
_RETRY_DELAY = 0.5
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_MAX_BACKOFF = 4.0


class LangSearchClient:
    """Thin async wrapper around the LangSearch REST API."""

    def __init__(self, *, timeout: float = 8.0) -> None:
        settings = get_settings()
        self._api_key = settings.langsearch_api_key
        self._base_url = settings.langsearch_base_url.rstrip("/")
        self._timeout = timeout

    @staticmethod
    def _retry_after_seconds(response: Any) -> float | None:
        """Seconds the server asked us to wait, or None when it did not say.

        A daily token quota error will not clear before the UTC reset, so a
        large Retry-After means retrying is pointless.
        """
        retry_after = response.headers.get("Retry-After") if response.headers else None
        if not retry_after:
            return None
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        """Exponential backoff with jitter, capped to the retry budget."""
        delay = _RETRY_DELAY * (2 ** (attempt - 1))
        return min(delay + random.uniform(0, _RETRY_DELAY), _MAX_BACKOFF)

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
            
            data = None
            search_failed = False
            for attempt in range(1, _MAX_RETRIES + 1):
                response = await client.post(self._base_url, json=payload, headers=headers)

                if response.status_code not in _RETRY_STATUSES:
                    response.raise_for_status()
                    data = response.json()
                    break

                search_failed = True
                retry_after = self._retry_after_seconds(response)
                if retry_after is not None and retry_after > _MAX_BACKOFF:
                    logger.error(
                        "LangSearch %d asks for %.0fs; allowance is exhausted for this UTC day, "
                        "not retrying (resets 00:00 UTC)",
                        response.status_code, retry_after,
                    )
                    return []

                if attempt >= _MAX_RETRIES:
                    logger.error(
                        "LangSearch %d after %d attempts for query: %s",
                        response.status_code, attempt, query[:50],
                    )
                    return []

                delay = retry_after if retry_after is not None else self._backoff_seconds(attempt)
                logger.warning(
                    "LangSearch %d, retrying in %.1fs (attempt %d/%d)",
                    response.status_code, delay, attempt, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
            
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
