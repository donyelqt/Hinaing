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
    ) -> list[WebDocument]:
        if not self._api_key:
            logger.warning("LangSearch API key missing; returning empty result set")
            return []

        payload: dict[str, Any] = {
            "query": self._enrich_query(query=query, focus_areas=focus_areas),
            "count": max(1, limit),  # Removed hard cap; let API enforce its own limits
            "summary": True,
        }
        freshness = self._map_freshness(time_window)
        if freshness:
            payload["freshness"] = freshness

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
                        logger.error("LangSearch rate limited, max retries exceeded for query: %s", query[:50])
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

            documents: list[WebDocument] = []
            for item in self._extract_web_results(data):
                try:
                    # SANITIZE at extraction time BEFORE reranking
                    # Prevents indirect prompt injection and poisoned documents from getting high scores
                    snippet = item.get("snippet") or item.get("summary") or ""
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

            if not documents:
                return documents

            try:
                return self._local_rerank(
                    query=payload["query"],
                    documents=documents,
                )
            except Exception:  # pragma: no cover - rerank must not break primary search
                logger.exception("Local BM25 rerank failed; returning original ranking")
                return documents

    @staticmethod
    def _enrich_query(query: str, focus_areas: list[str] | None) -> str:
        """Keep query clean for precise search results.
        
        Previously added Facebook page filters which diluted search precision.
        Now returns the query as-is for accurate results.
        """
        # Return query unchanged for precise, accurate search results
        # The semantic reranker will handle relevance scoring
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


    @staticmethod
    def _local_rerank(query: str, documents: list[WebDocument]) -> list[WebDocument]:
        if len(documents) <= 1:
            return documents
        from rank_bm25 import BM25Okapi

        def _tok(text: str) -> list[str]:
            return re.findall(r"[a-z0-9]+", (text or "").lower())

        corpus = [_tok(f"{d.title} {d.snippet}") for d in documents]
        tokenized = _tok(query)
        if not tokenized or all(not len(t) for t in corpus):
            return documents
        scores = BM25Okapi(corpus).get_scores(tokenized)
        order = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
        return [documents[i] for i in order]

    async def rerank(self, *, query: str, documents: list[WebDocument]) -> list[WebDocument]:
        """Public method to rerank documents using semantic relevance.
        
        Args:
            query: The search query to rank documents against.
            documents: List of WebDocument objects to rerank.
            
        Returns:
            Reranked list of WebDocument objects with semantic_relevance_score in metadata.
        """
        if not documents:
            return documents
            
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                return await self._rerank_documents(
                    client=client,
                    query=query,
                    documents=documents,
                )
            except Exception as exc:
                logger.exception("Semantic rerank failed; returning original order: %s", exc)
                return documents
