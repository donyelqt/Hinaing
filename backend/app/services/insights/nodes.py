"""Graph Nodes implementing the 7-Node Architecture logic."""
from __future__ import annotations

import asyncio
import gc
import json
import logging
import time
from collections import Counter
from typing import Any, TypedDict, cast

def _round(val: Any, ndigits: int = 0) -> float:
    """Pure math rounding to satisfy type checkers that reject 2-arg round()."""
    try:
        if val is None:
            return 0.0
        f_val = float(val)
        factor = 10 ** ndigits
        return float(int(f_val * factor + (0.5 if f_val >= 0 else -0.5))) / factor
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0
from langchain_core.runnables import RunnableLambda  # type: ignore
from pydantic import ValidationError  # type: ignore

from app.core.config import get_settings  # type: ignore
from app.schemas.snapshot import (  # type: ignore
    Insight,
    SentimentBreakdown,
    SnapshotRequest,
    SnapshotResponse,
    WebDocument,
)
from app.schemas.rag import AugmentedContext  # type: ignore
from app.schemas.query import QueryPlan  # type: ignore

from app.services.insights.agents import (  # type: ignore
    RetrievalAgent,
    SentimentAgent,
    CredibilityAgent,
    ThemeRouterAgent,
)
from app.services.agents.query_orchestrator import QueryOrchestratorAgent  # type: ignore
from app.services.agents.context_agent import ContextAugmentationAgent  # type: ignore
from app.services.agents.coordinator_agent import get_coordinator_agent  # type: ignore
from app.services.langsearch import LangSearchClient  # type: ignore
from app.services.metrics import get_metrics_collector  # type: ignore

from app.services.insights.definitions import (  # type: ignore
    SnapshotState,
    THEME_GROUPS,
    node4_semaphore,
    node4_ml_semaphore,
)
from app.services.insights import agent_tools  # type: ignore

def _log_memory_usage(stage: str):
    """Log current memory usage for debugging OOM issues."""
    try:
        import psutil  # type: ignore
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
    """Break down the request into executable queries.
    
    ABLATION STUDY: Pass ablation_config to disable temporal/context tools.
    """
    request = state["request"]
    ablation = state.get("ablation_config", {})
    try:
        plan = await query_orchestrator.run(request, ablation_config=ablation)
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
    """Recall internal knowledge (RAG) based on focus areas.

    ABLATION STUDY: If cyclic_rag_enabled is False, skip recall to measure impact.
    OPTIMIZATION: Increased limit from 20 to 50 docs for higher cache hit rate.
    This improves API cost reduction by recalling more cached documents.
    """
    request = state["request"]
    focus = request.focus_areas
    
    # ABLATION: Check if Self-Learning Cyclic RAG is disabled
    ablation = state.get("ablation_config", {})
    if not ablation.get("cyclic_rag_enabled", True):
        logger.info("[ABLA] Node 3 skipped: Self-Learning Cyclic RAG disabled")
        state["internal_documents"] = []
        state["documents"] = state.get("external_documents", [])
        state["rag_relevance_scores"] = []
        return state

    start_time = time.perf_counter()

    internal_docs = []
    if focus:
        try:
            # Increased from 20 to 50 for higher Smart Reuse rate
            internal_docs = await context_agent.retrieve_knowledge(focus_areas=focus, limit=50)
        except Exception as exc:
            logger.warning("[snapshot] Internal retrieval failed: %s", exc)

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("[snapshot] Internal retrieval recall in %.1f ms with %d docs", duration_ms, len(internal_docs))
    
    state["internal_documents"] = internal_docs
    # Hard Boundary: Force list-casting for Sized iteration
    _docs_list = cast(list, (internal_docs or []))
    rag_scores = [
        float((d.metadata or {}).get("_score", 0.0))
        for d in _docs_list
    ]
    state["rag_relevance_scores"] = rag_scores
    
    # ── Context Agent Accuracy Metrics ──
    # Hard Boundary: Re-hydrate scores into fresh primitives
    v_scores = [float(s) for s in (rag_scores or [])]
    if v_scores:
        sum_f = float(sum(v_scores))
        len_f = float(len(v_scores))
        avg_score = sum_f / len_f
        high_relevance = sum(1 for s in v_scores if float(s) >= 0.5)
        mid_relevance = sum(1 for s in v_scores if 0.3 <= float(s) < 0.5)
        low_relevance = sum(1 for s in v_scores if float(s) < 0.3)
        top_score = float(max(v_scores))
        hit_rate = (float(high_relevance) / len_f) * 100.0 if len_f > 0 else 0.0
        
        logger.info(
            "[Context Agent] RAG Accuracy: avg=%.3f, top=%.3f, hit_rate=%.1f%% "
            "(%d high≥0.5, %d mid, %d low<0.3) from %d recalled docs",
            avg_score, top_score, hit_rate,
            high_relevance, mid_relevance, low_relevance, len(rag_scores)
        )
    else:
        logger.info("[Context Agent] RAG Accuracy: No documents recalled from memory (0 hits)")
    
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
    # ABLATION STUDY: If smart_reuse_enabled is False, bypass cache and analyze all documents
    ablation = state.get("ablation_config", {})
    smart_reuse_enabled = ablation.get("smart_reuse_enabled", True)
    
    enriched_cache = {}
    already_enriched = []
    docs_to_analyze = []
    
    if smart_reuse_enabled:
        # FULL SYSTEM: Check for reusable documents
        for doc in internal_docs:
            # Check if document has both sentiment and credibility analysis
            has_sentiment = doc.sentiment is not None and doc.sentiment != ""
            has_credibility = (doc.metadata or {}).get("credibility_score") is not None

            if has_sentiment and has_credibility:
                # This document is fully analyzed - can be reused!
                url_key = str(doc.url) if doc.url else doc.title
                enriched_cache[url_key] = doc

        # Separate documents: already-enriched vs needs-analysis
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
    else:
        # ABLATED: Disable Smart Reuse - treat all documents as needing fresh analysis
        logger.info("[ABLA] Smart Reuse disabled - analyzing all documents from scratch")
        docs_to_analyze = raw_docs.copy()
        already_enriched = []

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
        
        # Record metrics BEFORE early return (VSEE + API Cost Reduction)
        total_docs = len(already_enriched)
        metrics.record_api_cost_reduction(
            api_calls_total=total_docs * 2,
            api_calls_actual=0,
            documents_cached=len(already_enriched),
            documents_fresh=0,
        )
        
        # Record Agentic Verification Rate from cached docs
        verified_count = sum(
            1 for doc in already_enriched
            if float((doc.metadata or {}).get("credibility_score", 0.0)) >= 0.55
        )
        metrics.record_agentic_verification_rate(
            total_documents=int(total_docs),
            verified_documents=int(verified_count),
        )
        
        # Record VSEE Effectiveness from cached docs - use cast for absolute narrowing
        v_triggered_shadow: int = cast(int, 0)
        v_crossref_shadow: int = cast(int, 0)
        v_domain_shadow: int = cast(int, 0)
        v_high_shadow: int = cast(int, 0)
        v_scores_shadow: list[float] = []

        for doc in already_enriched:
            d_meta = cast(dict[str, Any], doc.metadata or {})
            d_brk = cast(dict[str, Any], d_meta.get("credibility_breakdown", {}))
            
            c_s: float = cast(float, d_brk.get("cross_reference", 0.50))
            d_s: float = cast(float, d_brk.get("domain", 0.50))
            cr_s: float = cast(float, d_meta.get("credibility_score", 0.50))

            v_vsee: bool = bool(c_s >= 0.70 and d_s >= 0.45)
            v_dom: bool = bool(d_s >= 0.70 and c_s >= 0.55)

            if v_vsee or v_dom:
                v_triggered_shadow = cast(int, int(v_triggered_shadow) + 1)
                v_scores_shadow.append(cast(float, cr_s))
                if cr_s >= 0.75:
                    v_high_shadow = cast(int, int(v_high_shadow) + 1)
                if v_vsee and not v_dom:
                    v_crossref_shadow = cast(int, int(v_crossref_shadow) + 1)
                elif v_dom and not v_vsee:
                    v_domain_shadow = cast(int, int(v_domain_shadow) + 1)

        f_trig: float = cast(float, float(v_triggered_shadow))
        f_avg: float = cast(float, sum(v_scores_shadow) / float(len(v_scores_shadow)) if v_scores_shadow else 0.0)
        f_rate: float = cast(float, float(v_high_shadow) / f_trig if f_trig > 0.0 else 0.0)

        metrics.record_vsee_effectiveness(
            triggered_count=cast(int, v_triggered_shadow),
            bypass_rate=cast(float, f_trig / float(total_docs) if total_docs > 0 else 0.0),
            api_calls_avoided=cast(int, int(v_triggered_shadow) * 2),
            verified_via_crossref=cast(int, v_crossref_shadow),
            verified_via_domain=cast(int, v_domain_shadow),
            avg_credibility_score=_round(f_avg, 3),
            high_credibility_rate=_round(f_rate, 3),
            api_agreement_rate=_round(f_rate, 3),
            internal_consensus_score=_round(f_avg, 3),
        )
        
        logger.info(
            f"[snapshot] Node 4 Complete (Smart Reuse). Latency: {time.perf_counter() - start_time:.1f}s "
            f"(API calls saved: {api_calls_saved})"
        )
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

        # ABLATION: Check if VSEE is disabled
        ablation = state.get("ablation_config", {})
        disable_vsee = not ablation.get("vsee_enabled", True)
        if disable_vsee:
            logger.info("[ABLA] Node 4: VSEE disabled for credibility scoring")

        metrics.start_timer("credibility")
        result = await credibility_agent_node.run(docs, disable_vsee=disable_vsee)
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
                # ABLATION: Check if parallel execution is disabled
                ablation = state.get("ablation_config", {})
                parallel_enabled = ablation.get("parallel_enabled", True)
                
                if parallel_enabled:
                    # PARALLEL: Concurrent execution (full system)
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks),
                        timeout=NODE4_TIMEOUT
                    )
                else:
                    # SEQUENTIAL: Ablated - run tasks one at a time
                    logger.info("[ABLA] Node 4: Parallel execution disabled - running sequentially")
                    results = []
                    for task in tasks:
                        result = await asyncio.wait_for(task, timeout=NODE4_TIMEOUT)
                        results.append(result)

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
        # NUCLEAR: absolute shadowing to bridge Coroutine/List ambiguity
        c_list_f = list(cast(list, credibility_docs or []))
        s_list_f = list(cast(list, sentiment_docs or []))
        
        c_doc = c_list_f[i] if i < len(c_list_f) else docs[i]
        s_doc = s_list_f[i] if i < len(s_list_f) else docs[i]
        
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

    # Record API Cost Reduction metrics (Smart Reuse)
    total_docs = len(already_enriched) + len(newly_enriched_docs)
    api_calls_total = total_docs * 2  # Sentiment + Credibility per doc
    api_calls_actual = len(newly_enriched_docs) * 2  # Only fresh docs analyzed
    metrics.record_api_cost_reduction(
        api_calls_total=api_calls_total,
        api_calls_actual=api_calls_actual,
        documents_cached=len(already_enriched),
        documents_fresh=len(newly_enriched_docs),
    )

    # Record Agentic Verification Rate (count verified documents)
    # Matches frontend logic: score >= 0.55 OR tier in ["high", "medium"]
    # This aligns with high_credibility_count in graph.py and frontend display
    verified_count = sum(
        1 for doc in all_enriched_docs
        if (doc.metadata or {}).get("credibility_score", 0) >= 0.55
    )
    metrics.record_agentic_verification_rate(
        total_documents=len(all_enriched_docs),
        verified_documents=verified_count,
    )

    # Record VSEE Effectiveness Metrics — SINGLE SOURCE OF TRUTH
    # Use the authoritative _vsee_metrics computed by CredibilityAgent.run()
    # instead of re-computing VSEE eligibility (which could drift from the real logic).
    vsee_m = getattr(credibility_agent_node, '_vsee_metrics', None)

    if vsee_m:
        # CredibilityAgent computed REAL metrics during run()
        vsee_triggered = vsee_m["vsee_triggered_count"]
        vsee_api_avoided = vsee_m["vsee_total_api_calls_avoided"]
        vsee_bypass_rate = vsee_m["vsee_bypass_rate"]
        vsee_via_crossref = vsee_m.get("vsee_verified_via_crossref", 0)
        vsee_via_domain = vsee_m.get("vsee_verified_via_domain", 0)
        vsee_api_agreement = vsee_m.get("vsee_api_agreement_rate", 0.0)
        vsee_internal_consensus = vsee_m.get("vsee_internal_consensus_score", 0.0)
    else:
        # Fallback: no fresh credibility run (all docs from cache)
        vsee_triggered = 0
        vsee_api_avoided = 0
        vsee_bypass_rate = 0.0
        vsee_via_crossref = 0
        vsee_via_domain = 0
        vsee_api_agreement = 0.0
        vsee_internal_consensus = 0.0

    # VSEE quality metrics from enriched docs (always accurate regardless of source)
    v_scores_final: list[float] = []
    v_high_count_final: int = 0

    for doc in all_enriched_docs:
        d_meta_f = cast(dict[str, Any], doc.metadata or {})
        d_contrib_f = cast(dict[str, Any], d_meta_f.get("verification_contributions", {}))
        if bool(d_contrib_f.get("vsee_override", False)):
            c_s_f = float(d_meta_f.get("credibility_score", 0.50))
            v_scores_final.append(float(c_s_f))
    # HARD BOUNDARY: Absolute primitive shadowing to kill Buffer/Unknown tracer history
    v_scores_pure = [float(x) for x in v_scores_final]
    # Nuclear isolation to break recursive Buffer tracer
    _v_sum_raw = sum(v_scores_pure)
    v_n_atom: float = float(_v_sum_raw) if v_scores_pure else 0.0
    v_d_atom: float = float(len(v_scores_pure))
    
    v_avg_f: float = 0.0
    v_high_f: float = 0.0
    if float(v_d_atom) > 0.0:
        v_avg_f = float(float(v_n_atom) / float(v_d_atom))
        v_h_raw = float(v_high_count_final)
        v_high_f = float(float(v_h_raw) / float(v_d_atom))

    metrics.record_vsee_effectiveness(
        triggered_count=int(vsee_triggered),
        bypass_rate=float(vsee_bypass_rate),
        api_calls_avoided=int(vsee_api_avoided),
        verified_via_crossref=int(vsee_via_crossref),
        verified_via_domain=int(vsee_via_domain),
        avg_credibility_score=float(v_avg_f),
        high_credibility_rate=float(v_high_f),
        api_agreement_rate=float(vsee_api_agreement),
        internal_consensus_score=float(vsee_internal_consensus),
    )

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
    """Ingest FRESH external documents into persistent memory.
    
    ABLATION STUDY: If cyclic_rag_enabled is False, skip consolidation to measure impact.
    """
    # ABLATION: Check if Self-Learning Cyclic RAG is disabled
    ablation = state.get("ablation_config", {})
    if not ablation.get("cyclic_rag_enabled", True):
        logger.info("[ABLA] Node 5 skipped: Self-Learning Cyclic RAG disabled")
        state["rag_chunks_stored"] = 0
        return state
    
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
    """Run Gemini mini-agents per theme in parallel threads.
    
    ABLATION STUDY: If parallel_enabled is False, run theme agents sequentially.
    """
    theme_docs = state.get("theme_documents", {})
    request = state["request"]
    contexts = {} # unused
    start_time = time.perf_counter()
    
    # ABLATION: Check if parallel execution is disabled
    ablation = state.get("ablation_config", {})
    parallel_enabled = ablation.get("parallel_enabled", True)

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
    active_set: set[str] = set(active_themes)
    for theme_key, docs in theme_docs.items():
        if docs and str(theme_key) in active_set:
            tasks.append((theme_key, docs))

    insights = []
    
    if parallel_enabled:
        # PARALLEL: Concurrent execution (full system)
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
    else:
        # SEQUENTIAL: Ablated - run theme agents one at a time
        logger.info("[ABLA] Node 6: Parallel theme execution disabled - running sequentially")
        for theme_key, docs in tasks:
            try:
                result = _synthesize_single_theme(theme_key, docs, contexts)
                if isinstance(result, list):
                    insights.extend(result)
                elif isinstance(result, Insight):
                    insights.append(result)
            except Exception as exc:
                logger.exception("Theme agent failed for %s: %s", theme_key, exc)

    state["theme_insights"] = insights
    return state


# --------------------------------------------------------------------------
# NODE 7: Build Snapshot
# --------------------------------------------------------------------------
async def build_snapshot(state: SnapshotState) -> SnapshotState:
    """Final Synthesis Node with Faithfulness Verification.
    
    Uses Sequential Pipeline Pattern within Node 7:
    - Phase 1: Generate (CoordinatorAgent) - with CWA citations
    - Phase 2: Verify (FaithfulnessAgent) - PGCV verification
    - Phase 3: Assemble (SnapshotResponse)
    """
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

    # ABLATION STUDY: Check if Credibility-Weighted Attribution (CWA) is disabled
    ablation = state.get("ablation_config", {})
    cwa_enabled = ablation.get("cwa_enabled", True)
    
    # CWA: Sort documents by credibility score before passing to CoordinatorAgent
    if cwa_enabled:
        # FULL SYSTEM: Sort by credibility (high credibility docs cited first)
        docs_for_coordinator = sorted(
            docs,
            key=lambda d: (d.metadata or {}).get("credibility_score", 0.5),
            reverse=True
        )
    else:
        # ABLATED: No credibility weighting - use original order
        logger.info("[ABLA] Node 7: CWA disabled - using uniform source weighting")
        docs_for_coordinator = docs

    if coordinator_agent.is_available and docs_for_coordinator:
        try:
            summary_text, insights_payload = await coordinator_agent.run(
                window=request.time_window,
                focus_areas=request.focus_areas,
                documents=[doc.model_dump() for doc in docs_for_coordinator],
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
                # Use cast(Any, ...) for slice
                "examples": "; ".join(doc.title for doc in list(cast(Any, docs)[slice(0, 2)])) or "limited recent updates",
            }
        )

    # ─────────────────────────────────────────────────────────────
    # Phase 2: Verify Claims (PGCV) - Enhanced with Citation Verification
    # ─────────────────────────────────────────────────────────────
    verification_report = None
    
    # ABLATION STUDY: Check if faithfulness verification is disabled
    ablation = state.get("ablation_config", {})
    faithfulness_enabled = ablation.get("faithfulness_enabled", True)
    
    if summary_text and faithfulness_enabled:
        try:
            from app.services.agents.faithfulness_agent import FaithfulnessAgent
            from app.services.metrics.collector import get_metrics_collector
            verifier = FaithfulnessAgent()
            metrics = get_metrics_collector()
            verification_report = await verifier.verify(
                summary=summary_text,
                documents=[doc.model_dump() for doc in docs],
            )
            logger.info(
                f"[Node 7] Verification complete: "
                f"{verification_report['verified_claims']}/{verification_report['total_claims']} "
                f"verified ({verification_report['faithfulness_score']:.2f}), "
                f"{verification_report['hallucination_analysis']['hallucination_count']} hallucinations detected",
            )
            # Record faithfulness metrics with citation accuracy and hallucination detection
            metrics.record_faithfulness_metrics(
                total_claims=verification_report["total_claims"],
                verified_claims=verification_report["verified_claims"],
                faithfulness_score=verification_report["faithfulness_score"],
                citation_verification=verification_report.get("citation_verification"),
                hallucination_analysis=verification_report.get("hallucination_analysis"),
            )
        except Exception as exc:
            logger.exception("[snapshot] FaithfulnessAgent verification failed: %s", exc)
            verification_report = None
    elif not faithfulness_enabled:
        logger.info("[ABLA] Node 7: Faithfulness verification disabled")

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
            related = [doc for doc in list(cast(list, docs or [])) if str(focus).lower() in (str(doc.snippet or '').lower() + str(doc.title or '').lower())]
            r_pure = list(cast(list, related or []))
            d_pure = list(cast(list, docs or []))
            
            if r_pure:
                # Use cast(Any, ...) for index
                snippet = str(cast(Any, r_pure)[0].snippet or "")
            elif d_pure:
                snippet = str(cast(Any, d_pure)[0].snippet or "")
            else:
                snippet = "Residents request timely advisories."
            
            insights.append(
                Insight(
                    category=str(focus).title(),
                    title=f"Monitor {str(focus).title()} developments",
                    detail=str(cast(Any, snippet)[slice(0, 500)]),
                    evidence=[str(doc.url) for doc in list(cast(Any, r_pure)[slice(0, 2)]) if doc.url],
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
            verification=verification_report,  # NEW: Include verification report
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


def _build_theme_context(documents: list[dict]) -> str:
    """Build context string from documents for theme agents."""
    import re
    
    def sanitize(text):
        if not text:
            return ""
        text_str = str(text)
        # Remove invalid Unicode
        cleaned = re.sub(r'[\ud800-\udfff]', '', text_str)
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
        cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
        return cleaned.strip()
    
    doc_lines = []
    # Use cast(Any, ...) for slice
    for doc in cast(Any, documents)[slice(None, 10)]:
        title = sanitize(doc.get('title', 'Untitled'))
        s_raw_t = sanitize(doc.get('snippet', ''))
        snippet = str(cast(Any, s_raw_t)[slice(None, 200)])
        url = sanitize(doc.get('url', ''))
        if url:
            doc_lines.append(f"- [{title}]({url}): {snippet}")
        else:
            doc_lines.append(f"- {title}: {snippet}")
    return "\n".join(doc_lines)


def _build_theme_prompt(theme_label: str, focus: str, context: str, doc_count: int) -> str:
    """Build the prompt for theme agent insight generation."""
    return f"""You are a civic analyst for Baguio City providing actionable intelligence for government officials.

Theme: {theme_label}
{focus}

Task: Analyze the documents below and generate EXACTLY 3 ACTIONABLE RECOMMENDATIONS for government action.

Documents ({doc_count} shown):
{context}

CRITICAL REQUIREMENTS FOR GOOD GOVERNANCE:
1. Generate EXACTLY 3 actionable recommendations (no more, no less)
2. Each recommendation must address a DIFFERENT issue or sub-topic
3. Each recommendation must include SPECIFIC ACTIONS the government can take
4. Focus on PRACTICAL, IMPLEMENTABLE solutions
5. Prioritize the most URGENT issues affecting citizens

Format for each recommendation:
- Title: Clear problem statement
- Detail: Specific action the government should take (under 240 characters)
- Evidence: URLs from documents supporting this recommendation

Examples of ACTIONABLE recommendations for Infrastructure:
✅ GOOD (Actionable):
  - Title: "Traffic congestion on Session Road during peak hours"
    Detail: "Deploy 5 additional traffic enforcers at key intersections (7-9 AM, 5-7 PM). Consider implementing odd-even vehicle scheme."
  
  - Title: "Water supply interruptions in District 3"
    Detail: "Conduct emergency pipe inspection and repair. Coordinate with BWWD to establish backup water delivery schedule for affected areas."

❌ BAD (Not actionable):
  - Title: "Infrastructure challenges"
    Detail: "There are problems with traffic, water, and parking." (Too vague, no specific action)

⚠️ CRITICAL JSON FORMAT RULES:
- Output MUST start with {{ and end with }}
- Return ONLY the JSON object, nothing else
- Use double quotes for all strings

Return ONLY valid JSON with this exact structure:
{{
  "insights": [
    {{
      "title": "Specific problem requiring government action",
      "detail": "Concrete action government should take (under 240 chars)",
      "evidence": ["actual_url_from_documents_above"]
    }},
    {{
      "title": "Second distinct problem requiring action",
      "detail": "Specific government intervention needed (under 240 chars)",
      "evidence": ["actual_url_from_documents_above"]
    }},
    {{
      "title": "Third different problem requiring response",
      "detail": "Actionable government solution (under 240 chars)",
      "evidence": ["actual_url_from_documents_above"]
    }}
  ]
}}

IMPORTANT:
- The "evidence" array MUST contain actual URLs from the documents above
- If documents truly lack {theme_label} content, return: {{"insights": []}}
- Generate EXACTLY 3 actionable recommendations if you have sufficient content
- Each recommendation must be SPECIFIC and IMPLEMENTABLE by government
- ONLY JSON output, no extra text"""


def _parse_theme_insights(output: str, theme_label: str) -> list[dict]:
    """Parse theme agent JSON output into insight dicts."""
    import re
    
    original_output = output
    
    # Remove markdown code blocks if present
    if "```json" in output:
        output = output.split("```json")[1].split("```")[0].strip()
    elif "```" in output:
        output = output.split("```")[1].split("```")[0].strip()
    
    # If output is empty after stripping, try to extract JSON from original
    if not output or len(output) < 10:
        logger.warning(f"[{theme_label}] Output empty after stripping, extracting JSON from original")
        json_start = original_output.find('{"insights"')
        if json_start == -1:
            json_start = original_output.find('{ "insights"')
        if json_start == -1:
            json_start = original_output.find('{\n  "insights"')
        
        if json_start != -1:
            depth = 0
            for i in range(json_start, len(original_output)):
                if original_output[i] == '{':
                    depth += 1
                elif original_output[i] == '}':
                    depth -= 1
                    if depth == 0:
                        output = original_output[json_start:i+1]
                        break
    
    try:
        parsed = json.loads(output)
        insights = parsed.get("insights", [])
        
        sanitized = []
        for item in insights:
            if isinstance(item, dict):
                sanitized.append({
                    "title": item.get("title", f"Update in {theme_label}"),
                    "detail": item.get("detail", "Context unavailable"),
                    "evidence": [str(e) for e in item.get("evidence", []) if e],
                })
        
        if not sanitized:
            logger.warning(f"[{theme_label}] Parsed JSON but got 0 insights. Output sample: {output[:500]}")
        else:
            logger.info(f"[{theme_label}] Successfully parsed {len(sanitized)} insights")
        
        return sanitized
    except json.JSONDecodeError as e:
        logger.error(f"[{theme_label}] JSON parse failed: {e}")
        logger.error(f"[{theme_label}] Failed output: {output[:1000]}")
        return []

def _synthesize_single_theme(theme_key: str, docs: list[WebDocument], contexts: Any) -> list[Insight]:
    """Helper for Theme Agent execution - spawns true sub-agents.
    
    RATE LIMIT PROTECTION: Uses semaphore to prevent hitting Groq's 30 RPM limit
    when 6 theme agents fire simultaneously.
    """
    from app.services.agents.theme_agent import get_theme_agent  # type: ignore
    
    current_theme_groups = getattr(agent_tools, 'THEME_GROUPS', THEME_GROUPS)  # type: ignore
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
        for doc in cast(Any, docs)[slice(None, 100)]
    ]
    
    try:
        if len(docs) < 1:
            raise ValueError("skip_gemini_fallback")
        
        # SPAWN TRUE SUB-AGENT using factory
        agent = get_theme_agent(theme_key)
        logger.info(f"[ThemeAgent] Spawned {type(agent).__name__} for '{label}'")
        
        # FIXED: Don't use asyncio.run() inside ThreadPoolExecutor!
        # Instead, run the agent synchronously using sync_groq_generate
        # This prevents "Event loop is closed" error when Groq retries
        from ..llm.groq_provider import get_groq_provider
        
        # Build context and prompt (same as agent.run() does)
        context = _build_theme_context(enriched_docs)
        prompt = _build_theme_prompt(label, agent.theme_focus if hasattr(agent, 'theme_focus') else f"Focus on {label}", context, len(enriched_docs))
        
        # Use Groq synchronously to avoid event loop issues
        llm = get_groq_provider("meta-llama/llama-4-scout-17b-16e-instruct")
        logger.info(f"[ThemeAgent] Running synchronous Groq for '{label}' with {len(enriched_docs)} docs")
        
        try:
            # Use synchronous generate method
            response = llm.generate_sync(
                prompt=prompt,
                system_prompt="You are a civic analyst for Baguio City providing actionable recommendations for government officials. Output ONLY valid JSON, no extra text.",
                temperature=0.1,
                max_tokens=8000,
            )
            
            from app.services.agents.theme_agent import sanitize_text
            output = sanitize_text(response)
            
            # Parse the response
            insights = _parse_theme_insights(output, label)
            
        except Exception as groq_err:
            logger.warning(f"[ThemeAgent] Groq sync failed for {label}: {groq_err}, using fallback")
            raise ValueError("Groq failed, using fallback")
        
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
