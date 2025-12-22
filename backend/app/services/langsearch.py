"""LangSearch API client wrapper."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from ..core.config import get_settings
from pydantic import ValidationError

from ..schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)
_RERANK_MODEL = "langsearch-reranker-v1"
_MAX_RETRIES = 5
_RETRY_DELAY = 0.3  # Faster initial retry; backoff: 0.3s, 0.6s, 1.2s, 2.4s, 4.8s


class LangSearchClient:
    """Thin async wrapper around the LangSearch REST API."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        settings = get_settings()
        self._api_key = settings.langsearch_api_key
        self._base_url = settings.langsearch_base_url.rstrip("/")
        self._rerank_url = settings.langsearch_rerank_url.rstrip("/")
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
            # Retry with exponential backoff for rate limits (429)
            data = None
            for attempt in range(1, _MAX_RETRIES + 1):
                response = await client.post(self._base_url, json=payload, headers=headers)
                
                if response.status_code == 429:
                    if attempt < _MAX_RETRIES:
                        delay = _RETRY_DELAY * (2 ** (attempt - 1))  # Exponential: 1.5s, 3s, 6s
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
            
            if data is None:
                return []

            documents: list[WebDocument] = []
            for item in self._extract_web_results(data):
                try:
                    documents.append(
                        WebDocument(
                            title=item.get("name") or item.get("title") or "Untitled result",
                            snippet=item.get("snippet") or item.get("summary") or "",
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
                return await self._rerank_documents(
                    client=client,
                    query=payload["query"],
                    documents=documents,
                )
            except Exception as exc:  # pragma: no cover - rerank must not break primary search
                logger.exception("LangSearch semantic rerank failed; returning original ranking: %s", exc)
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

    async def _rerank_documents(
        self,
        *,
        client: httpx.AsyncClient,
        query: str,
        documents: list[WebDocument],
    ) -> list[WebDocument]:
        if not self._rerank_url or not documents:
            return documents

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        docs_payload = [f"{doc.title}\n\n{doc.snippet}" for doc in documents]
        payload: dict[str, Any] = {
            "model": _RERANK_MODEL,
            "query": query,
            "documents": docs_payload,
            "top_n": len(docs_payload),
            "return_documents": False,
        }

        # Retry with exponential backoff for rate limits (429)
        data = None
        for attempt in range(1, _MAX_RETRIES + 1):
            response = await client.post(self._rerank_url, json=payload, headers=headers)
            
            if response.status_code == 429:
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "Rerank rate limited (429), retrying in %.1fs (attempt %d/%d)",
                        delay, attempt, _MAX_RETRIES
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.warning("Rerank rate limited, max retries exceeded, skipping rerank")
                    return documents
            
            response.raise_for_status()
            data = response.json()
            break
        
        if data is None:
            return documents

        results = data.get("results")
        if not isinstance(results, list):
            return documents

        ranked: list[WebDocument] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            score = item.get("relevance_score")
            if not isinstance(index, int) or not (0 <= index < len(documents)):
                continue
            doc = documents[index]
            metadata = dict(doc.metadata)
            if isinstance(score, (int, float)):
                metadata["semantic_relevance_score"] = float(score)
            ranked.append(doc.model_copy(update={"metadata": metadata}))

        return ranked or documents

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
