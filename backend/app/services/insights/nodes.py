"""Graph Nodes implementing the 7-Node Architecture logic."""
from __future__ import annotations

import asyncio
import gc
import json
import logging
import time
from collections import Counter
from typing import TypedDict
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
        plan = query_orchestrator.run(request)
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
    return state


# --------------------------------------------------------------------------
# NODE 4: Unified Analysis
# --------------------------------------------------------------------------
async def label_sentiment_and_analyze(state: SnapshotState) -> SnapshotState:
    """Parallel execution of Sentiment, Credibility, and Theme Routing.
    
    PERFORMANCE OPTIMIZATION: 
    1. Relevance-Aware Sorting: Ensures 'Deep-Clean' logic hits the best docs.
    2. Parallel Batching: Fully utilizes unlocked semaphores.
    """
    raw_docs = state.get("documents", [])
    request = state["request"]
    start_time = time.perf_counter()
    metrics = get_metrics_collector()
    
    if not raw_docs:
        state["enriched"] = []
        state["credibility_notes"] = {}
        state["theme_documents"] = {key: [] for key in THEME_GROUPS}
        logger.info("[snapshot] label_sentiment_and_analyze skipped (no docs)")
        return state

    # 100x CTO OPTIMIZATION: Sort by relevance score so Top-20 Deep-Clean is accurate
    # Documents from Internal Memory have '_score'. External docs from Reranker are already ordered.
    docs = sorted(
        raw_docs, 
        key=lambda d: (d.metadata or {}).get("_score", 0.0), 
        reverse=True
    )

    async def run_sentiment():
        metrics.start_timer("sentiment")
        # Now truly parallel due to increased Semaphore in definitions.py
        async with node4_ml_semaphore:
            result = await asyncio.to_thread(sentiment_agent.run, docs)
            gc.collect()
            metrics.stop_timer("sentiment")
            return result

    async def run_credibility():
        metrics.start_timer("credibility")
        # CredibilityAgent now has its own internal Deep-Clean Sampling for speed
        result = await credibility_agent_node.run(docs)
        metrics.stop_timer("credibility")
        return result

    async def run_theme_router():
        metrics.start_timer("theme_routing")
        # Fast keyword-based routing
        result = await asyncio.to_thread(theme_router_agent.run, docs, request)
        metrics.stop_timer("theme_routing")
        return result

    NODE4_TIMEOUT = 240  # Increased from 180 to handle large document sets with Tavily verification + embeddings
    
    try:
        async with node4_semaphore:
            logger.info(f"[snapshot] Starting High-Throughput Analysis on {len(docs)} docs")
            sentiment_docs, credibility_docs, theme_docs = await asyncio.wait_for(
                asyncio.gather(
                    run_sentiment(),
                    run_credibility(),
                    run_theme_router(),
                ),
                timeout=NODE4_TIMEOUT
            )
    except asyncio.TimeoutError:
        logger.error(f"[snapshot] Node 4 timeout after {NODE4_TIMEOUT}s - using partial fallback")
        sentiment_docs = [doc.model_copy(update={"sentiment": "neutral"}) for doc in docs]
        credibility_docs = docs
        theme_docs = theme_router_agent.run(docs, request)

    gc.collect()
    
    # SPEED OPTIMIZATION: Single-pass merge logic
    # sentiment_docs and credibility_docs have the SAME order because we sorted them at start
    enriched_docs = []
    credibility_notes = {}
    
    for i in range(len(docs)):
        s_doc = sentiment_docs[i]
        c_doc = credibility_docs[i]
        
        # Merge sentiment and credibility metadata
        merged_metadata = {
            **(c_doc.metadata or {}),
            **(s_doc.metadata or {})
        }
        
        enriched = c_doc.model_copy(update={
            "sentiment": s_doc.sentiment,
            "metadata": merged_metadata
        })
        enriched_docs.append(enriched)
        
        # Update notes for the domain
        domain = merged_metadata.get("source_domain", "unknown")
        score = merged_metadata.get("credibility_score", 0.5)
        credibility_notes[domain] = score
    
    state["enriched"] = enriched_docs
    state["credibility_notes"] = credibility_notes
    state["theme_documents"] = theme_docs
    
    logger.info(f"[snapshot] Node 4 Complete. Latency: {time.perf_counter() - start_time:.1f}s")
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
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    insights = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_synthesize_single_theme, theme_key, docs, contexts): theme_key
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
    docs = state.get("enriched", [])
    
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
    """Helper for Theme Agent execution."""
    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS
    meta = current_theme_groups.get(theme_key)
    label = meta["label"] if meta else theme_key.title()
    
    logger.info(f"[ThemeAgent] Starting synthesis for '{label}' with {len(docs)} documents")
    
    if not docs:
        logger.info(f"[ThemeAgent] {label} has no documents, skipping")
        return []
        
    internal_count = sum(1 for d in docs if (d.metadata or {}).get("source") == "internal_memory")
    
    enriched_docs = [
        {**doc.model_dump(), "url": str(doc.url) if doc.url else ""}
        for doc in docs[:100]
    ]

    evidence_seed = [str(doc.url) for doc in docs[:3] if doc.url]
    try:
        if len(docs) < 1:
            raise ValueError("skip_gemini_fallback")
        from ..agents.theme_agent import run_theme_agent

        prompt = (
            "You are a civic operations analyst for Baguio City. "
            f"Focus on the theme '{label}'. "
            "Write JSON with a key 'insights' containing a list of objects. Each object must have keys: "
            "'title', 'detail', 'evidence' (array of source URLs). "
            f"You have {len(docs)} documents ({internal_count} historical/memory, {len(docs)-internal_count} fresh). "
            "Identify distinct sub-issues. Do not merge unrelated problems. If there are multiple distinct risks, list them separately."
        )
        response = run_theme_agent(
            theme_label=label,
            prompt=prompt,
            documents=enriched_docs,
        )
        parsed = _parse_agent_json(response)
        
        logger.debug(f"[ThemeAgent] {label} parsed response type: {type(parsed)}")
        
        results = []
        
        # normalized parsing
        items = []
        if isinstance(parsed, dict) and "insights" in parsed and isinstance(parsed["insights"], list):
            items = parsed["insights"]
            logger.debug(f"[ThemeAgent] {label} found {len(items)} insights in dict format")
        elif isinstance(parsed, list):
            items = parsed
            logger.debug(f"[ThemeAgent] {label} found {len(items)} insights in list format")
        elif isinstance(parsed, dict) and "title" in parsed:
            items = [parsed]
            logger.debug(f"[ThemeAgent] {label} found 1 insight in single dict format")

        for item in items:
            title = item.get("title") or f"Update in {label}"
            detail = item.get("detail") or "Context unavailable"
            parsed_evidence = item.get("evidence")
            evidence = []
            if isinstance(parsed_evidence, list) and parsed_evidence:
                valid_urls = [str(url) for url in parsed_evidence if url and str(url).startswith("http")]
                if valid_urls:
                    evidence = valid_urls
            else:
                 # fallback to seed evidence if none specific provided
                 evidence = evidence_seed

            results.append(Insight(category=label, title=title, detail=detail[:500], evidence=evidence))
            
        if not results:
             # If parsing found nothing structured, use fallback
             raise ValueError("No structured insights found")
        
        # Validation: Log insight generation quality
        if len(results) < 3:
            logger.warning(
                f"[ThemeAgent] {label} has {len(docs)} docs but only {len(results)} insight(s). "
                f"Expected 3 insights. LLM may be over-merging issues or hit token limit."
            )
        elif len(results) == 3:
            logger.info(f"[ThemeAgent] {label} generated {len(results)} insights ✓ (target met)")
        else:
            logger.info(f"[ThemeAgent] {label} generated {len(results)} insights (exceeded target of 3)")

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
