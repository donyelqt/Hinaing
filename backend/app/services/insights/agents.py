"""Lightweight agent orchestrators for the insights workflow."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Sequence

from ...schemas.snapshot import SnapshotRequest, WebDocument
from ...schemas.query import QueryPlan, QueryTask
from .agent_tools import (
    search_web_documents,
    fetch_facebook_documents,
    fetch_reddit_documents,
    assign_sentiment,
    score_credibility,
    route_documents_by_theme,
    deduplicate_documents,
)
from ..agents.sentiment_agent import get_sentiment_agent

# Maximum documents to process (controls cost and latency)
MAX_DOCUMENTS = 30

logger = logging.getLogger(__name__)


@dataclass
class RetrievalAgent:
    """Agent that decides which platforms to pull documents from."""

    async def run(
        self,
        request: SnapshotRequest,
        query_plan: QueryPlan | None = None,
    ) -> list[WebDocument]:
        logger.info(
            "[retrieval_agent] planning",
            extra={
                "platforms": request.platforms,
                "focus": request.focus_areas,
                "queries": len(query_plan.queries) if query_plan else 0,
            },
        )

        tasks: list[asyncio.Task[list[WebDocument]]] = []
        if "web" in request.platforms:
            if query_plan and query_plan.queries:
                logger.info(
                    "[retrieval_agent] executing orchestrated web queries",
                    extra={"count": len(query_plan.queries)},
                )
                # Execute queries sequentially with delay to avoid rate limits
                for idx, task in enumerate(query_plan.queries):
                    if idx > 0:
                        await asyncio.sleep(1.5)  # 1.5s delay between queries to avoid 429
                    tasks.append(
                        asyncio.create_task(
                            search_web_documents(
                                request,
                                custom_query=task.query,
                            )
                        )
                    )
            else:
                logger.info("[retrieval_agent] invoking LangSearch tool (baseline)")
                tasks.append(asyncio.create_task(search_web_documents(request)))

        if "facebook" in request.platforms:
            logger.info("[retrieval_agent] invoking Facebook tool")
            tasks.append(asyncio.create_task(fetch_facebook_documents(request)))

        if "reddit" in request.platforms:
            # Pass query_plan to Reddit so it uses orchestrated queries
            if query_plan and query_plan.queries:
                logger.info("[retrieval_agent] invoking Reddit tool with orchestrated query")
                tasks.append(asyncio.create_task(
                    fetch_reddit_documents(request, query_plan=query_plan)
                ))
            else:
                logger.info("[retrieval_agent] invoking Reddit tool (baseline)")
                tasks.append(asyncio.create_task(fetch_reddit_documents(request)))

        if not tasks:
            return []

        documents: list[WebDocument] = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.exception("[retrieval_agent] data source failed", exc_info=result)
                continue
            documents.extend(result)

        # Global deduplication across all query results
        before_dedup = len(documents)
        documents = deduplicate_documents(documents)
        
        # Cap total documents to control cost/latency
        if len(documents) > MAX_DOCUMENTS:
            logger.info(
                "[retrieval_agent] capping documents: %d -> %d",
                len(documents), MAX_DOCUMENTS
            )
            documents = documents[:MAX_DOCUMENTS]

        logger.info(
            "[retrieval_agent] collected %d documents (before dedup: %d)",
            len(documents), before_dedup
        )
        return documents


@dataclass
class SentimentAgent:
    """AI-powered agent that labels sentiment using Gemini."""

    use_ai: bool = True  # Set to False to use rule-based fallback

    def run(self, documents: Sequence[WebDocument]) -> list[WebDocument]:
        logger.info("[sentiment_agent] labeling %d documents (AI=%s)", len(documents), self.use_ai)
        
        if self.use_ai:
            try:
                agent = get_sentiment_agent()
                return agent.analyze_batch(list(documents))
            except Exception as exc:
                logger.warning("[sentiment_agent] Gemini failed, falling back to rules: %s", exc)
                return assign_sentiment(list(documents))
        
        return assign_sentiment(list(documents))


@dataclass
class CredibilityAgent:
    """Agent that scores domain credibility.
    
    Now uses EnhancedCredibilityAgent with:
    - Domain trust tiers
    - Google Fact Check API
    - Gemini LLM analysis
    - Content quality signals
    """
    
    use_enhanced: bool = True

    async def run(self, documents: Sequence[WebDocument]) -> list[WebDocument]:
        """Score credibility and return enriched documents."""
        logger.info("[credibility_agent] scoring %d documents", len(documents))
        
        if self.use_enhanced:
            try:
                from ..agents.credibility_agent import get_credibility_agent
                agent = get_credibility_agent()
                return await agent.run(list(documents))
            except Exception as exc:
                logger.warning("[credibility_agent] Enhanced failed, using fallback: %s", exc)
        
        # Fallback to simple heuristic scoring
        scored = score_credibility(list(documents))
        # Enrich documents with basic scores
        enriched = []
        for doc in documents:
            domain = doc.url.host if doc.url else "unknown"
            score = scored.get(domain, 0.5)
            enriched.append(doc.model_copy(update={
                "metadata": {
                    **(doc.metadata or {}),
                    "credibility_score": score,
                    "credibility_tier": "high" if score >= 0.8 else "medium" if score >= 0.6 else "low",
                }
            }))
        return enriched


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
