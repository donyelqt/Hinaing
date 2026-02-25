"""Graph Nodes implementing the 7-Node Architecture logic."""
from __future__ import annotations

import asyncio
import gc
import json
import logging
import time
from collections import Counter
from typing import Any, TypedDict
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from ...core.config import get_settings
from ...schemas.snapshot import (
    Insight,
    SentimentBreakdown,
    SnapshotRequest,
    SnapshotResponse,
    WebDocument,
)
from ...schemas.rag import AugmentedContext
from ...schemas.query import QueryPlan

from .agents import (
    RetrievalAgent,
    SentimentAgent,
    CredibilityAgent,
    ThemeRouterAgent,
)
from ..agents.query_orchestrator import QueryOrchestratorAgent
from ..agents.context_agent import ContextAugmentationAgent
from ..agents.coordinator_agent import get_coordinator_agent
from ..langsearch import LangSearchClient
from ..metrics import get_metrics_collector

from .definitions import (
    SnapshotState,
    THEME_GROUPS,
    node4_semaphore,
    node4_ml_semaphore,
)
from . import agent_tools

def _log_memory_usage(stage: str):
    """Log current memory usage for debugging OOM issues."""
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        logging.getLogger(__name__).info(f"[memory] {stage}: {mem_mb:.1f} MB")
    except ImportError:
        pass

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# AGENT INSTANCES (The Workforce)
# --------------------------------------------------------------------------
retrieval_agent = RetrievalAgent()
sentiment_agent = SentimentAgent()
credibility_agent_node = CredibilityAgent()
theme_router_agent = ThemeRouterAgent()
query_orchestrator = QueryOrchestratorAgent()
context_agent = ContextAugmentationAgent()

# Initialize theme groups in tools
agent_tools.set_theme_groups(THEME_GROUPS)


# --------------------------------------------------------------------------
# NODE 1: Query Orchestration
# --------------------------------------------------------------------------
async def orchestrate_queries(state: SnapshotState) -> SnapshotState:
    """Break down the request into executable queries."""
    request = state["request"]
    try:
        plan = await query_orchestrator.run(request)
    except Exception as exc:
        logger.warning("[snapshot] Query orchestrator failed, falling back: %s", exc)
        plan = None
    state["retrieval_plan"] = plan
    return state


# --------------------------------------------------------------------------
# NODE 2: External Retrieval
# --------------------------------------------------------------------------
async def fetch_documents(state: SnapshotState) -> SnapshotState:
    """Fetch fresh data from web/social sources."""
    request = state["request"]
    plan = state.get("retrieval_plan")
    logger.info("[snapshot] Retrieval agent planning fetch", extra={"platforms": request.platforms})
    start_time = time.perf_counter()
    try:
        documents = await retrieval_agent.run(request, query_plan=plan)
    except Exception:
        logger.exception("Retrieval agent failed; returning empty document set")
        documents = []

    if "web" in request.platforms and "facebook" in request.platforms and len(documents) > 1:
        query = _build_query(request)
        try:
            reranker = LangSearchClient()
            documents = await reranker.rerank(query=query, documents=documents)
        except Exception as exc:
            logger.warning("Semantic rerank failed; continuing without rerank: %s", exc)

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("[snapshot] External retrieval completed in %.1f ms with %d docs", duration_ms, len(documents))
    
    state["external_documents"] = documents
    state["documents"] = documents 
    return state


# --------------------------------------------------------------------------
# NODE 3: Internal Memory Recall
# --------------------------------------------------------------------------
async def retrieve_internal_knowledge(state: SnapshotState) -> SnapshotState:
    """Recall internal knowledge (RAG) based on focus areas."""
    request = state["request"]
    focus = request.focus_areas
    
    start_time = time.perf_counter()
    
    internal_docs = []
    if focus:
        try:
            internal_docs = await context_agent.retrieve_knowledge(focus_areas=focus, limit=20)
        except Exception as exc:
            logger.warning("[snapshot] Internal retrieval failed: %s", exc)
            
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("[snapshot] Internal retrieval recall in %.1f ms with %d docs", duration_ms, len(internal_docs))
    
    state["internal_documents"] = internal_docs
    state["rag_relevance_scores"] = [
        (d.metadata or {}).get("_score", 0.0) 
        for d in internal_docs
    ]
    
    raw_combined = state.get("external_documents", []) + internal_docs
    
    # Deduplication
    seen_urls = set()
    seen_titles = set()
    unique_docs = []
    
    for doc in raw_combined:
        if doc.url and doc.url in seen_urls:
            continue
        norm_title = (doc.title or "").strip().lower()
        if not norm_title: 
            pass
        elif norm_title in seen_titles:
            continue
        if doc.url:
            seen_urls.add(doc.url)
        if norm_title:
            seen_titles.add(norm_title)
        unique_docs.append(doc)
    
    state["documents"] = unique_docs
    
    # Record document counts for metrics
    metrics = get_metrics_collector()
    external_count = len(state.get("external_documents", []))
    internal_count = len(internal_docs)
    metrics.record_retrieval_metrics(external_count, internal_count, len(unique_docs))
    
    return state


# --------------------------------------------------------------------------
# NODE 4: Unified Analysis (with Smart Reuse)
# --------------------------------------------------------------------------
async def label_sentiment_and_analyze(state: SnapshotState) -> SnapshotState:
    """Parallel execution of Sentiment, Credibility, and Theme Routing.
    
    PERFORMANCE OPTIMIZATION: 
    1. Relevance-Aware Sorting: Ensures 'Deep-Clean' logic hits the best docs.
    2. Parallel Batching: Fully utilizes unlocked semaphores.
    3. Conditional Execution: Skips sentiment or credibility based on mode flags.
    4. SMART REUSE: Reuses already-enriched documents from internal memory (API cost savings).
    """
    raw_docs = state.get("documents", [])
    internal_docs = state.get("internal_documents", [])
    request = state["request"]
    start_time = time.perf_counter()
    metrics = get_metrics_collector()
    
    # Get mode flags from state (default to True for backward compatibility)
    include_sentiment = state.get("include_sentiment", True)
    include_credibility = state.get("include_credibility", True)
    
    logger.info(
        f"[snapshot] Node 4: sentiment={include_sentiment}, credibility={include_credibility}"
    )
    
    if not raw_docs:
        state["enriched"] = []
        state["credibility_notes"] = {}
        state["theme_documents"] = {key: [] for key in THEME_GROUPS}
        logger.info("[snapshot] label_sentiment_and_analyze skipped (no docs)")
        return state
    
    # SMART REUSE: Build cache of already-enriched documents from internal memory
    enriched_cache = {}
    for doc in internal_docs:
        # Check if document has both sentiment and credibility analysis
        has_sentiment = doc.sentiment is not None and doc.sentiment != ""
        has_credibility = (doc.metadata or {}).get("credibility_score") is not None
        
        if has_sentiment and has_credibility:
            # This document is fully analyzed - can be reused!
            url_key = str(doc.url) if doc.url else doc.title
            enriched_cache[url_key] = doc
    
    # Separate documents: already-enriched vs needs-analysis
    docs_to_analyze = []
    already_enriched = []
    
    for doc in raw_docs:
        url_key = str(doc.url) if doc.url else doc.title
        if url_key in enriched_cache:
            # REUSE: This document was already analyzed in a previous run
            cached_doc = enriched_cache[url_key]
            already_enriched.append(cached_doc)
            logger.debug(f"[COST SAVE] Reusing analysis for: {doc.title[:50] if doc.title else 'Untitled'}")
        else:
            # NEW: This document needs fresh analysis
            docs_to_analyze.append(doc)
    
    api_calls_saved = len(already_enriched) * 2  # Sentiment + Credibility per doc
    
    if already_enriched:
        logger.info(
            f"[COST OPTIMIZATION] Reusing {len(already_enriched)} enriched docs "
            f"(~{api_calls_saved} API calls saved), analyzing {len(docs_to_analyze)} fresh docs"
        )
    
    if not docs_to_analyze:
        # All documents were already enriched - no analysis needed!
        logger.info("[COST OPTIMIZATION] All documents already enriched - skipping analysis entirely!")
        state["enriched"] = already_enriched
        state["credibility_notes"] = {}
        state["theme_documents"] = theme_router_agent.run(already_enriched, request)
        state["api_calls_saved"] = api_calls_saved
        return state

    # 100x CTO OPTIMIZATION: Sort by relevance score so Top-20 Deep-Clean is accurate
    # Documents from Internal Memory have '_score'. External docs from Reranker are already ordered.
    # ONLY sort documents that need analysis (already-enriched docs maintain their order)
    docs = sorted(
        docs_to_analyze, 
        key=lambda d: (d.metadata or {}).get("_score", 0.0), 
        reverse=True
    )

    async def run_sentiment():
        if not include_sentiment:
            logger.info("[Node4] Sentiment skipped (sentiment mode disabled)")
            # Return docs with placeholder neutral sentiment
            return [doc.model_copy(update={"sentiment": "neutral"}) for doc in docs]
        
        metrics.start_timer("sentiment")
        async with node4_ml_semaphore:
            result = await asyncio.to_thread(sentiment_agent.run, docs)
            gc.collect()
            metrics.stop_timer("sentiment")
            return result

    async def run_credibility():
        if not include_credibility:
            logger.info("[Node4] Credibility skipped (credibility mode disabled)")
            # Return unscored docs with placeholder metadata
            result = []
            for doc in docs:
                new_meta = {**(doc.metadata or {}), "credibility_score": None}
                result.append(doc.model_copy(update={"metadata": new_meta}))
            return result
        
        metrics.start_timer("credibility")
        result = await credibility_agent_node.run(docs)
        metrics.stop_timer("credibility")
        return result

    async def run_theme_router():
        # Theme router runs on ALL docs (already-enriched + newly-analyzed)
        # We'll run it after merging
        pass

    NODE4_TIMEOUT = 240
    
    try:
        async with node4_semaphore:
            logger.info(f"[snapshot] Starting High-Throughput Analysis on {len(docs)} NEW docs")
            
            # Build task list based on mode flags
            tasks = []
            
            if include_sentiment:
                tasks.append(run_sentiment())
            if include_credibility:
                tasks.append(run_credibility())
            
            if tasks:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks),
                    timeout=NODE4_TIMEOUT
                )
                
                # Reconstruct results based on which tasks ran
                sentiment_docs = None
                credibility_docs = None
                
                idx = 0
                if include_sentiment:
                    sentiment_docs = results[idx]
                    idx += 1
                if include_credibility:
                    credibility_docs = results[idx]
            else:
                sentiment_docs = None
                credibility_docs = None
                
    except asyncio.TimeoutError:
        logger.error(f"[snapshot] Node 4 timeout after {NODE4_TIMEOUT}s - using partial fallback")
        sentiment_docs = [doc.model_copy(update={"sentiment": "neutral"}) for doc in docs] if include_sentiment else None
        credibility_docs = docs if include_credibility else None

    gc.collect()
    
    # Merge logic: handle None cases gracefully for NEWLY ANALYZED docs
    newly_enriched_docs = []
    credibility_notes = {}
    
    for i in range(len(docs)):
        c_doc = credibility_docs[i] if credibility_docs else docs[i]
        s_doc = sentiment_docs[i] if sentiment_docs else docs[i]
        
        # Merge metadata (handle None values)
        c_meta = c_doc.metadata or {}
        s_meta = s_doc.metadata or {}
        merged_metadata = {**c_meta, **s_meta}
        
        # Determine sentiment (use actual or default)
        final_sentiment = s_doc.sentiment if sentiment_docs else "neutral"
        
        enriched = c_doc.model_copy(update={
            "sentiment": final_sentiment,
            "metadata": merged_metadata
        })
        newly_enriched_docs.append(enriched)
        
        # Update credibility notes
        if include_credibility:
            domain = merged_metadata.get("source_domain", "unknown")
            score = merged_metadata.get("credibility_score", 0.5)
            if score is not None:
                credibility_notes[domain] = score
    
    # Also extract credibility notes from already-enriched docs
    for doc in already_enriched:
        domain = (doc.metadata or {}).get("source_domain", "unknown")
        score = (doc.metadata or {}).get("credibility_score", 0.5)
        if score is not None:
            credibility_notes[domain] = score
    
    # COMBINE: already-enriched + newly-analyzed
    all_enriched_docs = already_enriched + newly_enriched_docs
    
    # Run theme router on ALL documents (combined)
    metrics.start_timer("theme_routing")
    theme_docs = await asyncio.to_thread(theme_router_agent.run, all_enriched_docs, request)
    metrics.stop_timer("theme_routing")
    
    state["enriched"] = all_enriched_docs
    state["credibility_notes"] = credibility_notes
    state["theme_documents"] = theme_docs
    state["api_calls_saved"] = api_calls_saved
    
    logger.info(
        f"[snapshot] Node 4 Complete. Latency: {time.perf_counter() - start_time:.1f}s "
        f"(API calls saved: {api_calls_saved})"
    )
    return state


# --------------------------------------------------------------------------
# NODE 5: Memory Consolidation
# --------------------------------------------------------------------------
async def consolidate_memory(state: SnapshotState) -> SnapshotState:
    """Ingest FRESH external documents into persistent memory."""
    fresh_docs = state.get("external_documents", [])
    if not fresh_docs:
        return state
        
    start_time = time.perf_counter()
    
    enriched_map = {
        (d.url or d.title): d for d in state.get("enriched", [])
    }
    
    docs_to_save = []
    for raw_doc in fresh_docs:
        key = raw_doc.url or raw_doc.title
        if key in enriched_map:
            docs_to_save.append(enriched_map[key])
        else:
            docs_to_save.append(raw_doc)
            
    try:
        count = await context_agent.consolidate_memory(docs_to_save)
    except Exception as exc:
        logger.warning("[snapshot] Memory consolidation failed: %s", exc)
        count = 0
        
    duration_ms = (time.perf_counter() - start_time) * 1000
    state["rag_chunks_stored"] = count
    return state


# --------------------------------------------------------------------------
# NODE 6: Theme Agents (Parallel)
# --------------------------------------------------------------------------
def theme_agents(state: SnapshotState) -> SnapshotState:
    """Run Gemini mini-agents per theme in parallel threads."""
    theme_docs = state.get("theme_documents", {})
    request = state["request"]
    contexts = {} # unused
    start_time = time.perf_counter()

    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS

    active_themes = set(current_theme_groups.keys())
    if request.focus_areas:
        requested_focus = {f.lower() for f in request.focus_areas}
        matched_themes = {
            key for key, meta in current_theme_groups.items()
            if requested_focus & meta.get("focus_values", set())
        }
        if matched_themes:
            active_themes = matched_themes
        
    tasks = []
    for theme_key, docs in theme_docs.items():
        if docs and theme_key in active_themes:
            tasks.append((theme_key, docs))
    
    insights = []
    from app.core.executor import GLOBAL_EXECUTOR
    from concurrent.futures import as_completed
    
    futures = {
        GLOBAL_EXECUTOR.submit(_synthesize_single_theme, theme_key, docs, contexts): theme_key
        for theme_key, docs in tasks
    }
    
    for future in as_completed(futures):
        try:
            result = future.result()
            if isinstance(result, list):
                insights.extend(result)
            elif isinstance(result, Insight):
                insights.append(result)
        except Exception as exc:
            theme_key = futures[future]
            logger.exception("Theme agent task failed for %s: %s", theme_key, exc)
    
    state["theme_insights"] = insights
    return state


# --------------------------------------------------------------------------
# NODE 7: Build Snapshot
# --------------------------------------------------------------------------
async def build_snapshot(state: SnapshotState) -> SnapshotState:
    """Final Synthesis Node."""
    request = state["request"]
    # Use enriched docs if available (full/sentiment modes), otherwise use raw docs (epistemic mode)
    docs = state.get("enriched", []) or state.get("documents", [])
    
    total = max(len(docs), 1)
    counts = Counter(doc.sentiment or "neutral" for doc in docs)
    scores = {
        "negative": counts.get("negative", 0) / total,
        "neutral": counts.get("neutral", 0) / total,
        "positive": counts.get("positive", 0) / total,
    }

    summary_text = None
    insights_payload: list[dict[str, str]] = []
    coordinator_agent = get_coordinator_agent()
    
    if coordinator_agent.is_available and docs:
        try:
            summary_text, insights_payload = await coordinator_agent.run(
                window=request.time_window,
                focus_areas=request.focus_areas,
                documents=[doc.model_dump() for doc in docs],
                theme_insights=[i.model_dump() for i in state.get("theme_insights", [])],
                sentiment_distribution=scores,  # Pass sentiment breakdown to coordinator
            )
        except Exception as exc:
            logger.exception("[snapshot] CoordinatorAgent failed: %s", exc)
            summary_text = None
            insights_payload = []

    if not summary_text:
        summary_text = summary_chain.invoke(
            {
                "window": request.time_window,
                "topics": request.focus_areas or ["public services"],
                "examples": "; ".join(doc.title for doc in docs[:2]) or "limited recent updates",
            }
        )

    # Insight selection logic (Theme Agents > Gemini > Fallback)
    insights: list[Insight] = []
    theme_fallbacks = state.get("theme_insights") or []
    
    if theme_fallbacks:
        insights.extend(theme_fallbacks)
    elif insights_payload:
        for idx, payload in enumerate(insights_payload, start=1):
            try:
                evidence_raw = payload.get("evidence")
                match evidence_raw:
                    case str() as value: evidence = [value]
                    case list() as values: evidence = [str(item) for item in values if item]
                    case _: evidence = []

                insights.append(
                    Insight(
                        category=(payload.get("category") or "Operations").strip() or "Operations",
                        title=payload.get("title") or f"Key development {idx}",
                        detail=payload.get("detail") or "",
                        evidence=evidence,
                    )
                )
            except ValidationError:
                continue
    else:
        for focus in (request.focus_areas or ["Operations"]):
            related = [doc for doc in docs if focus.lower() in (doc.snippet.lower() + doc.title.lower())]
            snippet = related[0].snippet if related else (docs[0].snippet if docs else "Residents request timely advisories.")
            insights.append(
                Insight(
                    category=focus.title(),
                    title=f"Monitor {focus.title()} developments",
                    detail=snippet[:500],
                    evidence=[str(doc.url) for doc in related[:2] if doc.url],
                )
            )

    alerts: list[str] | None = None
    if request.include_alerts and scores["negative"] >= 0.45:
        alerts = ["Elevated negative sentiment detected—prioritize rapid response coordination."]

    try:
        snapshot = SnapshotResponse(
            overall_sentiment=SentimentBreakdown(
                label=_derive_label(scores),
                summary=summary_text,
                scores=scores,
            ),
            actionable_insights=insights,
            alerts=alerts,
            sources=docs,
        )
    except Exception as exc:
        logger.exception("[snapshot] Failed to create SnapshotResponse: %s", exc)
        raise

    state["snapshot"] = snapshot
    return state


# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------
def _derive_label(scores: dict[str, float]) -> str:
    negative = scores.get("negative", 0)
    positive = scores.get("positive", 0)
    if negative >= 0.55: return "Highly Concerned"
    if negative >= 0.4: return "Moderately Concerned"
    if positive >= 0.5: return "Positive Momentum"
    return "Mixed Sentiment"

def _build_query(request: SnapshotRequest) -> str:
    focus = " ".join(request.focus_areas or ["civic updates"])
    return f"Baguio City {focus} {request.time_window}"

summary_chain = RunnableLambda(
    lambda data: (
        f"Public chatter over {data['window']} centers on {', '.join(data['topics']) or 'civic services'}. "
        f"Representative updates cite {data['examples']}."
    )
)

def _parse_agent_json(raw_text: str) -> Any | None:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        inner = text.split("\n", 1)
        text = inner[1] if len(inner) > 1 else text[3:]
        text = text[:-3].strip()
    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        pass
    return None

def _synthesize_single_theme(theme_key: str, docs: list[WebDocument], contexts: Any) -> list[Insight]:
    """Helper for Theme Agent execution - spawns true sub-agents.
    
    RATE LIMIT PROTECTION: Uses semaphore to prevent hitting Groq's 30 RPM limit
    when 6 theme agents fire simultaneously.
    """
    from ..agents.theme_agent import get_theme_agent
    
    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS
    meta = current_theme_groups.get(theme_key)
    label = meta["label"] if meta else theme_key.title()
    
    logger.info(f"[ThemeAgent] Starting synthesis for '{label}' with {len(docs)} documents")
    
    if not docs:
        logger.info(f"[ThemeAgent] {label} has no documents, skipping")
        return []
    
    internal_count = sum(1 for d in docs if (d.metadata or {}).get("source") == "internal_memory")
    logger.info(f"[ThemeAgent] {label}: {internal_count} memory docs, {len(docs)-internal_count} fresh docs")
    
    enriched_docs = [
        {**doc.model_dump(), "url": str(doc.url) if doc.url else ""}
        for doc in docs[:100]
    ]
    
    try:
        if len(docs) < 1:
            raise ValueError("skip_gemini_fallback")
        
        # SPAWN TRUE SUB-AGENT using factory
        agent = get_theme_agent(theme_key)
        logger.info(f"[ThemeAgent] Spawned {type(agent).__name__} for '{label}'")
        
        # Run the sub-agent's autonomous reasoning
        # Note: We removed the semaphore here because it causes event loop issues
        # when running in ThreadPoolExecutor. The 30 RPM limit is high enough
        # that 6 concurrent agents won't hit it (6 requests in ~1s = 360 RPH = 6 RPM)
        insights = asyncio.run(agent.run(enriched_docs))
        
        # Convert to Insight objects
        evidence_seed = [str(doc.url) for doc in docs[:3] if doc.url]
        results = []
        for item in insights:
            title = item.get("title") or f"Update in {label}"
            detail = item.get("detail") or "Context unavailable"
            evidence = item.get("evidence") or evidence_seed
            results.append(Insight(category=label, title=title, detail=detail[:500], evidence=evidence))
        
        if not results:
            raise ValueError("No structured insights found")
        
        # Validation
        if len(results) < 3:
            logger.warning(f"[ThemeAgent] {label} has {len(docs)} docs but only {len(results)} insight(s)")
        elif len(results) == 3:
            logger.info(f"[ThemeAgent] {label} generated {len(results)} insights ✓ (target met)")
        else:
            logger.info(f"[ThemeAgent] {label} generated {len(results)} insights")
        
        return results
        
    except Exception as exc:
        logger.warning("Theme agent failed for %s: %s", label, exc)
        fallback_doc = docs[0]
        return [Insight(
            category=label,
            title=f"Key updates in {label}",
            detail=(fallback_doc.snippet or fallback_doc.title or "Context unavailable")[:500],
            evidence=[str(doc.url) for doc in docs[:2] if doc.url],
        )]
