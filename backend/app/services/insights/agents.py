"""Lightweight agent orchestrators for the insights workflow."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Sequence

from ...schemas.snapshot import SnapshotRequest, WebDocument
from .agent_tools import (
    search_web_documents,
    fetch_facebook_documents,
    assign_sentiment,
    score_credibility,
    route_documents_by_theme,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievalAgent:
    """Agent that decides which platforms to pull documents from."""

    async def run(self, request: SnapshotRequest) -> list[WebDocument]:
        logger.info(
            "[retrieval_agent] planning",
            extra={"platforms": request.platforms, "focus": request.focus_areas},
        )

        tasks: list[asyncio.Task[list[WebDocument]]] = []
        if "web" in request.platforms:
            logger.info("[retrieval_agent] invoking LangSearch tool")
            tasks.append(asyncio.create_task(search_web_documents(request)))

        if "facebook" in request.platforms:
            logger.info("[retrieval_agent] invoking Facebook tool")
            tasks.append(asyncio.create_task(fetch_facebook_documents(request)))

        if not tasks:
            return []

        documents: list[WebDocument] = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.exception("[retrieval_agent] data source failed", exc_info=result)
                continue
            documents.extend(result)

        logger.info("[retrieval_agent] collected %d documents", len(documents))
        return documents


@dataclass
class SentimentAgent:
    """Agent that labels sentiment for each document."""

    def run(self, documents: Sequence[WebDocument]) -> list[WebDocument]:
        logger.info("[sentiment_agent] labeling %d documents", len(documents))
        return assign_sentiment(list(documents))


@dataclass
class CredibilityAgent:
    """Agent that scores domain credibility."""

    def run(self, documents: Sequence[WebDocument]) -> dict[str, float]:
        logger.info("[credibility_agent] scoring %d documents", len(documents))
        return score_credibility(list(documents))


@dataclass
class ThemeRouterAgent:
    """Agent that clusters documents per configured theme group."""

    def run(self, documents: Sequence[WebDocument], request: SnapshotRequest) -> dict[str, list[WebDocument]]:
        logger.info(
            "[theme_router_agent] routing %d documents for focus areas %s",
            len(documents),
            request.focus_areas,
        )
        return route_documents_by_theme(list(documents), request.focus_areas)
