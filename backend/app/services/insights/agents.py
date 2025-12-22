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
MAX_DOCUMENTS = 100

logger = logging.getLogger(__name__)


@dataclass
class RetrievalAgent:
    """Agent that decides which platforms to pull documents from.
    
    Supports multi-query execution with diversity-aware merging:
    - Executes each query separately
    - Tracks which topic each result came from
    - Merges results ensuring topic diversity
    """

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

        # Track results by topic for diversity merging
        topic_results: dict[str, list[WebDocument]] = {}
        other_results: list[WebDocument] = []

        if "web" in request.platforms:
            if query_plan and query_plan.queries:
                # Use all queries from orchestrator (typically 6) for full topic diversity
                # Speed is maintained through parallel batching
                queries_to_run = query_plan.queries
                
                logger.info(
                    "[retrieval_agent] executing %d diverse web queries with PARALLEL batching",
                    len(queries_to_run),
                )
                
                # REBALANCED STRATEGY: Batch + Moderate Timeout
                # We cannot fire 6 queries at once or we get 429'd and drop topics.
                # We cannot use 10s timeout or we drop retrying queries.
                # Solution: Batches of 3 (Safe for API) + 20s Timeout (Safe for Retries)
                
                async def fetch_query(task, idx):
                    topic = task.topic or f"topic_{idx}"
                    try:
                        # Increased to 20s to allow for at least 3 retry cycles
                        docs = await asyncio.wait_for(
                            search_web_documents(
                                request,
                                custom_query=task.query,
                                limit=10,
                            ),
                            timeout=20.0
                        )
                        for doc in docs:
                            doc.metadata = {**(doc.metadata or {}), "_source_topic": topic}
                        logger.info("[retrieval_agent] query '%s' returned %d docs", topic, len(docs))
                        return topic, docs
                    except asyncio.TimeoutError:
                        logger.warning("[retrieval_agent] query '%s' timed out (20s)", topic)
                        return topic, []
                    except Exception as exc:
                        logger.warning("[retrieval_agent] query '%s' failed: %s", topic, exc)
                        return topic, []
                
                # OPTIMIZED: Smaller batches with staggered starts
                # Batch of 2 is safer for rate limits (reduced from 3)
                batch_size = 2
                for batch_start in range(0, len(queries_to_run), batch_size):
                    current_batch = queries_to_run[batch_start:batch_start + batch_size]
                    
                    logger.info("[retrieval_agent] executing batch %d-%d of %d", 
                               batch_start+1, batch_start+len(current_batch), len(queries_to_run))
                    
                    # Longer delay between batches for rate limit recovery (increased from 1.0s)
                    if batch_start > 0:
                        await asyncio.sleep(1.5)

                    # Staggered start: 400ms apart within batch (increased from 250ms)
                    # Total batch overhead: ~400ms, queries still run in parallel
                    async def staggered_fetch(task, idx, stagger_delay):
                        if stagger_delay > 0:
                            await asyncio.sleep(stagger_delay)
                        return await fetch_query(task, batch_start + idx)
                    
                    batch_results = await asyncio.gather(
                        *[staggered_fetch(task, i, i * 0.4) for i, task in enumerate(current_batch)],
                        return_exceptions=True
                    )
                    
                    for result in batch_results:
                        if isinstance(result, tuple):
                            topic, docs = result
                            topic_results.setdefault(topic, []).extend(docs)
            else:
                logger.info("[retrieval_agent] invoking LangSearch tool (baseline)")
                try:
                    docs = await search_web_documents(request)
                    other_results.extend(docs)
                except Exception as exc:
                    logger.warning("[retrieval_agent] baseline search failed: %s", exc)

        if "facebook" in request.platforms:
            logger.info("[retrieval_agent] invoking Facebook tool")
            try:
                docs = await fetch_facebook_documents(request)
                other_results.extend(docs)
            except Exception as exc:
                logger.warning("[retrieval_agent] Facebook failed: %s", exc)

        if "reddit" in request.platforms:
            logger.info("[retrieval_agent] invoking Reddit tool")
            try:
                docs = await fetch_reddit_documents(request, query_plan=query_plan)
                other_results.extend(docs)
            except Exception as exc:
                logger.warning("[retrieval_agent] Reddit failed: %s", exc)

        # Diversity-aware merging: interleave results from different topics
        documents = self._merge_with_diversity(topic_results, other_results)

        # Global deduplication
        before_dedup = len(documents)
        documents = deduplicate_documents(documents)
        
        # Cap total documents
        if len(documents) > MAX_DOCUMENTS:
            logger.info("[retrieval_agent] capping: %d -> %d", len(documents), MAX_DOCUMENTS)
            documents = documents[:MAX_DOCUMENTS]

        # Log topic distribution
        topic_counts = {}
        for doc in documents:
            topic = (doc.metadata or {}).get("_source_topic", "other")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        logger.info("[retrieval_agent] topic distribution: %s", topic_counts)

        logger.info(
            "[retrieval_agent] collected %d documents (before dedup: %d)",
            len(documents), before_dedup
        )
        return documents

    def _merge_with_diversity(
        self, 
        topic_results: dict[str, list[WebDocument]], 
        other_results: list[WebDocument]
    ) -> list[WebDocument]:
        """Interleave results from different topics for diversity.
        
        Strategy: Round-robin through topics, taking 2-3 docs at a time from each.
        This ensures no single topic dominates the results.
        """
        if not topic_results:
            return other_results
        
        merged: list[WebDocument] = []
        topics = list(topic_results.keys())
        indices = {topic: 0 for topic in topics}
        docs_per_round = 3  # Take 3 docs per topic per round
        
        # Round-robin through topics
        while True:
            added_this_round = False
            for topic in topics:
                docs = topic_results[topic]
                start_idx = indices[topic]
                end_idx = min(start_idx + docs_per_round, len(docs))
                
                if start_idx < len(docs):
                    merged.extend(docs[start_idx:end_idx])
                    indices[topic] = end_idx
                    added_this_round = True
            
            if not added_this_round:
                break
        
        # Add other results at the end
        merged.extend(other_results)
        
        logger.info("[retrieval_agent] diversity merge: %d topics, %d total docs", 
                   len(topics), len(merged))
        return merged


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
    """Semantic agent that routes documents to themes using embeddings + keyword fallback."""
    
    _semantic_agent = None  # Lazy-loaded semantic router

    def run(self, documents: Sequence[WebDocument], request: SnapshotRequest) -> dict[str, list[WebDocument]]:
        logger.info(
            "[theme_router_agent] routing %d documents for focus areas %s",
            len(documents),
            request.focus_areas,
        )
        
        # Lazy-load semantic router on first use
        if self._semantic_agent is None:
            from ..agents.theme_router_agent import get_theme_router_agent
            from .definitions import THEME_GROUPS
            self.__class__._semantic_agent = get_theme_router_agent(THEME_GROUPS)
        
        # Use semantic routing
        return self._semantic_agent.run(list(documents), request)
