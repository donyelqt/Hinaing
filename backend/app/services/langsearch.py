"""LangSearch API client wrapper."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from ..core.config import get_settings
from pydantic import ValidationError

from ..schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)


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
            "count": max(1, min(limit, 10)),
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
            response = await client.post(self._base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

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
        return documents

    @staticmethod
    def _enrich_query(query: str, focus_areas: list[str] | None) -> str:
        # The query already includes focus areas and location context from _build_query
        # Just pass it through to avoid double-processing
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
