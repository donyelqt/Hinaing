"""LangGraph workflow for generating sentiment snapshots."""

from __future__ import annotations

import gc
import json
import logging
import os
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
import asyncio
from pydantic import ValidationError


def _log_memory_usage(stage: str):
    """Log current memory usage for debugging OOM issues on Railway."""
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"[memory] {stage}: {mem_mb:.1f} MB")
    except ImportError:
        pass  # psutil not available

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
from ..nlp.gemini import gemini_client, GeminiClient
from ..agents.gemini import run_gemini_agent
# Note: build_focus_query and get_window_timedelta removed - query building now handled by QueryOrchestratorAgent
from .agent_tools import set_theme_groups

settings = get_settings()
logger = logging.getLogger(__name__)
if settings.langsmith_api_key:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    if settings.langsmith_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)


_node4_max_concurrency = max(1, int(os.getenv("NODE4_MAX_CONCURRENCY", "1")))
_node4_semaphore = asyncio.Semaphore(_node4_max_concurrency)
_node4_ml_max_concurrency = max(1, int(os.getenv("NODE4_ML_MAX_CONCURRENCY", "1")))
_node4_ml_semaphore = asyncio.Semaphore(_node4_ml_max_concurrency)


class SnapshotState(TypedDict, total=False):
    request: SnapshotRequest
    documents: list[WebDocument]  # Combined External + Internal
    internal_documents: list[WebDocument] # Internal Memory Recall
    external_documents: list[WebDocument] # Fresh External Retrieval
    enriched: list[WebDocument]
    theme_documents: dict[str, list[WebDocument]]
    augmented_contexts: dict[str, AugmentedContext]
    theme_insights: list[Insight]
    credibility_notes: dict[str, float]
    retrieval_plan: QueryPlan
    snapshot: SnapshotResponse


THEME_GROUPS = {
    "infrastructure": {
        "label": "Infrastructure",
        "focus_values": {"infrastructure"},
        "keywords": {
            # Core infrastructure terms
            "road", "traffic", "water", "power", "infrastructure", "bridge", "construction",
            # Baguio-specific from FOCUS_CONCERN_KEYWORDS
            "kennon", "session road", "bgh", "building", "outage", "substandard",
        },
    },
    "health": {
        "label": "Health & Wellness",
        "focus_values": {"health"},
        "keywords": {
            # Core health terms
            "hospital", "clinic", "health", "dengue", "covid", "medicine", "vaccine", "wellness",
            # Baguio-specific from FOCUS_CONCERN_KEYWORDS
            "bgh", "baguio general", "disease", "medical", "patient",
        },
    },
    "safety": {
        "label": "Public Safety",
        "focus_values": {"safety"},
        "keywords": {
            # Core safety terms
            "crime", "police", "fire", "landslide", "safety", "accident", "emergency", "security",
            # Baguio-specific from FOCUS_CONCERN_KEYWORDS
            "flood", "walkout", "protest", "rally", "incident", "student walkout", "youth rally",
        },
    },
    "tourism": {
        "label": "Tourism & Events",
        "focus_values": {"tourism"},
        "keywords": {
            # Core tourism terms
            "tourism", "tourist", "hotel", "festival", "event", "panagbenga", "visitor",
            # Baguio-specific from FOCUS_CONCERN_KEYWORDS
            "burnham", "overcrowding", "mines view", "camp john hay", "wright park",
        },
    },
    "economy": {
        "label": "Business & Economy",
        "focus_values": {"economy", "business"},
        "keywords": {
            # Core economy terms
            "market", "vendor", "livelihood", "economy", "business", "investment", "price",
            # Baguio-specific from FOCUS_CONCERN_KEYWORDS
            "mallification", "sm prime", "public market", "redevelopment", "displacement",
            "walkout", "protest", "students protest", "youth protest", "schools walkout",
        },
    },
    "environment": {
        "label": "Environment",
        "focus_values": {"environment"},
        "keywords": {
            # Core environment terms
            "garbage", "pollution", "environment", "rain", "waste", "tree", "green",
            # Baguio-specific from FOCUS_CONCERN_KEYWORDS
            "air quality", "flooding", "climate",
            "climate",
        },
    },
}

set_theme_groups(THEME_GROUPS)


retrieval_agent = RetrievalAgent()
sentiment_agent = SentimentAgent()
credibility_agent_node = CredibilityAgent()
theme_router_agent = ThemeRouterAgent()
query_orchestrator = QueryOrchestratorAgent()
context_agent = ContextAugmentationAgent()


async def orchestrate_queries(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    try:
        plan = query_orchestrator.run(request)
    except Exception as exc:
        logger.warning("[snapshot] Query orchestrator failed, falling back: %s", exc)
        plan = None
    state["retrieval_plan"] = plan
    return state


async def fetch_documents(state: SnapshotState) -> SnapshotState:
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
    # Initialize main documents list with external docs for now
    state["documents"] = documents 
    return state


async def retrieve_internal_knowledge(state: SnapshotState) -> SnapshotState:
    """Node 3: Recall internal knowledge (RAG) based on focus areas."""
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
    
    # Merge External + Internal into the main 'documents' list for Unified Analysis
    # We put external first to prioritize them in lists, but analysis sees all
    raw_combined = state.get("external_documents", []) + internal_docs
    
    # Deduplicate by URL (primary) and Title (secondary)
    seen_urls = set()
    seen_titles = set()
    unique_docs = []
    
    for doc in raw_combined:
        # Check URL uniqueness
        if doc.url and doc.url in seen_urls:
            continue
            
        # Check Title uniqueness (if URL missing or different but title same)
        # Normalize title for check
        norm_title = (doc.title or "").strip().lower()
        if not norm_title: 
            # If no title and no URL, we might skip or keep. Let's keep if it has snippet.
            # But usually web docs have one or the other.
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


async def label_sentiment_and_analyze(state: SnapshotState) -> SnapshotState:
    """Node 4: Unified Analysis (Sentiment + Credibility + Theme Routing).
    
    Now processes BOTH External (Fresh) and Internal (Memory) documents together!
    MEMORY OPTIMIZATION: Added GC and memory logging for Railway debugging.
    TIMEOUT PROTECTION: 150s total timeout for entire analysis node.
    """
    docs = state.get("documents", [])
    request = state["request"]
    start_time = time.perf_counter()
    
    _log_memory_usage("node4_start")
    
    if not docs:
        state["enriched"] = []
        state["credibility_notes"] = {}
        state["theme_documents"] = {key: [] for key in THEME_GROUPS}
        logger.info("[snapshot] label_sentiment_and_analyze skipped (no docs)")
        return state

    # Run ALL three operations in parallel:
    # 1. Sentiment analysis (sync, wrapped in thread)
    # 2. Credibility scoring (async)
    # 3. Theme routing (sync, wrapped in thread)

    async def run_sentiment():
        async with _node4_ml_semaphore:
            result = await asyncio.to_thread(sentiment_agent.run, docs)
            gc.collect()
            _log_memory_usage("node4_after_sentiment")
            return result

    async def run_credibility():
        async with _node4_ml_semaphore:
            result = await credibility_agent_node.run(docs)
            gc.collect()
            _log_memory_usage("node4_after_credibility")
            return result

    # TIMEOUT PROTECTION: 150 seconds max for entire analysis node
    NODE4_TIMEOUT = 150  # seconds
    
    try:
        async with _node4_semaphore:
            sentiment_docs, credibility_docs, theme_docs = await asyncio.wait_for(
                asyncio.gather(
                    run_sentiment(),
                    run_credibility(),
                    asyncio.to_thread(theme_router_agent.run, docs, request),
                ),
                timeout=NODE4_TIMEOUT
            )
    except asyncio.TimeoutError:
        logger.error(f"[snapshot] Node 4 timeout after {NODE4_TIMEOUT}s - using fallback")
        # Fallback: Use docs as-is with neutral sentiment
        sentiment_docs = [doc.model_copy(update={"sentiment": "neutral"}) for doc in docs]
        credibility_docs = docs
        theme_docs = theme_router_agent.run(docs, request)  # Theme routing is fast

    # MEMORY OPTIMIZATION: Force garbage collection after heavy processing
    gc.collect()
    _log_memory_usage("node4_after_analysis")
    
    # Merge sentiment labels into credibility-enriched documents
    # Create a mapping of URL -> sentiment data
    sentiment_map = {}
    for doc in sentiment_docs:
        key = str(doc.url) if doc.url else doc.title
        sentiment_map[key] = {
            "sentiment": doc.sentiment,
            "sentiment_metadata": {
                k: v for k, v in (doc.metadata or {}).items()
                if k.startswith("sentiment_") or k in ["roberta_prediction", "gemini_prediction", "model_agreement"]
            }
        }
    
    # Merge into credibility docs
    enriched_docs = []
    for doc in credibility_docs:
        key = str(doc.url) if doc.url else doc.title
        sentiment_data = sentiment_map.get(key, {})
        
        merged_metadata = {
            **(doc.metadata or {}),
            **sentiment_data.get("sentiment_metadata", {})
        }
        
        enriched_docs.append(doc.model_copy(update={
            "sentiment": sentiment_data.get("sentiment", doc.sentiment),
            "metadata": merged_metadata
        }))
    
    # Extract credibility notes for backward compatibility
    credibility_notes = {}
    for doc in enriched_docs:
        domain = doc.metadata.get("source_domain", "unknown") if doc.metadata else "unknown"
        score = doc.metadata.get("credibility_score", 0.5) if doc.metadata else 0.5
        credibility_notes[domain] = score
    
    state["enriched"] = enriched_docs
    state["credibility_notes"] = credibility_notes
    state["theme_documents"] = theme_docs
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "[snapshot] Unified Analysis completed in %.1f ms for %d total docs",
        duration_ms,
        len(docs),
    )
    return state


async def consolidate_memory(state: SnapshotState) -> SnapshotState:
    """Node 5: Memory Consolidation (Self-Learning Ingestion).
    
    Takes FRESH external documents and saves them to the Vector Store.
    Does NOT re-ingest internal memory documents.
    """
    # Only ingest docs that came from external sources
    # We can identify them by checking against the external_documents list
    # or relying on metadata if we propagated it cleanly.
    # The safest is to rely on state["external_documents"] which is pure.
    
    fresh_docs = state.get("external_documents", [])
    if not fresh_docs:
        logger.info("[snapshot] No fresh documents to consolidate")
        return state
        
    start_time = time.perf_counter()
    
    # We map sentiment/credibility data from 'enriched' back to 'fresh_docs' to save enhanced data?
    # Ideally yes, but for now we just save the raw content + basic metadata.
    # FUTURE UPGRADE: Save the Enriched/Scored version to memory!
    # Let's try to match them up from 'enriched' list
    
    enriched_map = {
        (d.url or d.title): d for d in state.get("enriched", [])
    }
    
    docs_to_save = []
    for raw_doc in fresh_docs:
        key = raw_doc.url or raw_doc.title
        if key in enriched_map:
            # Use the enriched version which has sentiment/credibility
            docs_to_save.append(enriched_map[key])
        else:
            docs_to_save.append(raw_doc)
            
    try:
        count = await context_agent.consolidate_memory(docs_to_save)
    except Exception as exc:
        logger.warning("[snapshot] Memory consolidation failed: %s", exc)
        count = 0
        
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("[snapshot] Consolidated %d new memories in %.1f ms", count, duration_ms)
    
    # No changes to state, just side-effect
    return state


def _parse_agent_json(raw_text: str) -> dict[str, str] | None:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        inner = text.split("\n", 1)
        text = inner[1] if len(inner) > 1 else text[3:]
        text = text[:-3].strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        logger.debug("Theme agent response not JSON: %s", raw_text)
    return None


# Minimum average relevance score to generate insights for a theme
# Lowered from 0.55 to 0.40 to allow more results through RAG filtering
MIN_RELEVANCE_THRESHOLD = 0.40


def _synthesize_single_theme(
    theme_key: str,
    docs: list[WebDocument],
    contexts: dict[str, AugmentedContext] | None,     # Unused now but kept for sig compatibility if needed
) -> Insight | None:
    """Synthesize insight for a single theme."""
    from . import agent_tools
    current_theme_groups = agent_tools.THEME_GROUPS or THEME_GROUPS
    meta = current_theme_groups.get(theme_key)
    label = meta["label"] if meta else theme_key.title()
    
    # Filter docs for this theme (already done by router)
    if not docs:
        return None
        
    # We can improve this by checking which docs are internal vs external
    internal_count = sum(1 for d in docs if (d.metadata or {}).get("source") == "internal_memory")
    
    enriched_docs = [
        {
            **doc.model_dump(),
            "url": str(doc.url) if doc.url else "",
        }
        for doc in docs[:100]
    ]

    evidence_seed = [str(doc.url) for doc in docs[:3] if doc.url]
    try:
        if len(docs) < 1: # lowered threshold
            raise ValueError("skip_gemini_fallback")
        from ..agents.theme_agent import run_theme_agent

        prompt = (
            "You are a civic operations analyst for Baguio City. "
            f"Focus on the theme '{label}'. "
            "Write JSON with keys 'title', 'detail', 'evidence' (array of source URLs). "
            f"You have {len(docs)} documents ({internal_count} historical/memory, {len(docs)-internal_count} fresh). "
            "Highlight actionable risk or opportunity, connecting fresh news with historical patterns if present."
        )
        response = run_theme_agent(
            theme_label=label,
            prompt=prompt,
            documents=enriched_docs,
        )
        parsed = _parse_agent_json(response)
        evidence = evidence_seed
        if parsed:
            title = parsed.get("title") or f"Key updates in {label}"
            detail = parsed.get("detail") or "Context unavailable"
            parsed_evidence = parsed.get("evidence")
            if isinstance(parsed_evidence, list) and parsed_evidence:
                # Filter out placeholder text and empty strings
                valid_urls = [
                    str(item) for item in parsed_evidence 
                    if item and str(item).startswith("http")
                ]
                if valid_urls:
                    evidence = valid_urls
                # If LLM returned invalid URLs, fall back to evidence_seed
        else:
            fallback_doc = max(
                docs,
                key=lambda d: (d.metadata or {}).get("semantic_relevance_score", 0.0),
                default=docs[0],
            )
            title = f"Key updates in {label}"
            detail = (fallback_doc.snippet or fallback_doc.title or "Context unavailable")[:500]
        return Insight(
            category=label,
            title=title,
            detail=detail[:500],
            evidence=evidence,
        )
    except Exception as exc:
        logger.warning("Theme agent failed for %s: %s", label, exc)
        fallback_doc = docs[0]
        return Insight(
            category=label,
            title=f"Key updates in {label}",
            detail=(fallback_doc.snippet or fallback_doc.title or "Context unavailable")[:500],
            evidence=[str(doc.url) for doc in docs[:2] if doc.url],
        )


def theme_agents(state: SnapshotState) -> SnapshotState:
    """Run Gemini mini-agents per theme to craft insights in parallel."""
    theme_docs = state.get("theme_documents", {})
    # Contexts are no longer passed explicitly, implicitly in docs
    contexts = {} 
    request = state["request"]
    start_time = time.perf_counter()

    from . import agent_tools
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
                if isinstance(result, Insight):
                    insights.append(result)
            except Exception as exc:
                theme_key = futures[future]
                logger.exception("Theme agent task failed for %s: %s", theme_key, exc)
    duration_ms = (time.perf_counter() - start_time) * 1000
    state["theme_insights"] = insights
    return state


def _derive_label(scores: dict[str, float]) -> str:
    negative = scores.get("negative", 0)
    positive = scores.get("positive", 0)
    if negative >= 0.55:
        return "Highly Concerned"
    if negative >= 0.4:
        return "Moderately Concerned"
    if positive >= 0.5:
        return "Positive Momentum"
    return "Mixed Sentiment"


def _build_query(request: SnapshotRequest) -> str:
    """Build a search query for semantic reranking."""
    focus = " ".join(request.focus_areas or ["civic updates"])
    return f"Baguio City {focus} {request.time_window}"


summary_chain = RunnableLambda(
    lambda data: (
        f"Public chatter over {data['window']} centers on {', '.join(data['topics']) or 'civic services'}. "
        f"Representative updates cite {data['examples']}."
    )
)


async def build_snapshot(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    docs = state.get("enriched", [])
    logger.info(
        "[snapshot] Building snapshot",
        extra={
            "platforms": request.platforms,
            "time_window": request.time_window,
            "focus_areas": request.focus_areas,
            "doc_count": len(docs),
        },
    )
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
        logger.info("[snapshot] CoordinatorAgent generating narrative", extra={"docs_used": len(docs)})
        try:
            summary_text, insights_payload = await coordinator_agent.run(
                window=request.time_window,
                focus_areas=request.focus_areas,
                documents=[doc.model_dump() for doc in docs],
                theme_insights=[i.model_dump() for i in state.get("theme_insights", [])],
            )
            logger.info("[snapshot] CoordinatorAgent completed successfully")
        except Exception as exc:
            logger.exception("[snapshot] CoordinatorAgent failed: %s", exc)
            summary_text = None
            insights_payload = []

    if not summary_text:
        logger.info("[snapshot] Using fallback summary chain")
        summary_text = summary_chain.invoke(
            {
                "window": request.time_window,
                "topics": request.focus_areas or ["public services"],
                "examples": "; ".join(doc.title for doc in docs[:2]) or "limited recent updates",
            }
        )
    logger.info("[snapshot] Summary text ready: %s", summary_text[:100] if summary_text else "None")

    # Primary: Use theme insights which are already balanced by theme
    insights: list[Insight] = []
    theme_fallbacks = state.get("theme_insights") or []
    
    if theme_fallbacks:
        # Use theme insights as primary source (they're already balanced)
        logger.info("[snapshot] Using %d theme-generated insights", len(theme_fallbacks))
        insights.extend(theme_fallbacks)
    elif insights_payload:
        # Only use Gemini insights if no theme insights available
        logger.info("[snapshot] Using %d Gemini-generated insights", len(insights_payload))
        for idx, payload in enumerate(insights_payload, start=1):
            try:
                evidence_raw = payload.get("evidence")
                match evidence_raw:
                    case str() as value:
                        evidence = [value]
                    case list() as values:
                        evidence = [str(item) for item in values if item]
                    case _:
                        evidence = []

                insights.append(
                    Insight(
                        category=(payload.get("category") or "Operations").strip() or "Operations",
                        title=payload.get("title") or f"Key development {idx}",
                        detail=payload.get("detail") or "",
                        evidence=evidence,
                    )
                )
            except ValidationError as exc:  # pragma: no cover - defensive against LLM drift
                logger.debug("Skipping malformed Gemini insight: %s", exc)
                continue
    else:
        # Last resort: generate basic insights from focus areas
        logger.info("[snapshot] Generating fallback insights from focus areas")
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
        alerts = [
            "Elevated negative sentiment detected—prioritize rapid response coordination.",
        ]

    logger.info("[snapshot] Creating SnapshotResponse with %d insights", len(insights))
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
        logger.info("[snapshot] SnapshotResponse created successfully")
    except Exception as exc:
        logger.exception("[snapshot] Failed to create SnapshotResponse: %s", exc)
        raise

    state["snapshot"] = snapshot
    logger.info("[snapshot] build_snapshot completed successfully")
    return state


graph = StateGraph(SnapshotState)
graph.add_node("orchestrate_queries", orchestrate_queries)
graph.add_node("fetch_documents", fetch_documents)
graph.add_node("retrieve_internal_knowledge", retrieve_internal_knowledge) # NODE 3: Memory Recall
graph.add_node("label_sentiment_and_analyze", label_sentiment_and_analyze) # NODE 4: Unified Analysis
graph.add_node("consolidate_memory", consolidate_memory) # NODE 5: Memory Ingestion
graph.add_node("theme_agents", theme_agents) # NODE 6
graph.add_node("build_snapshot", build_snapshot) # NODE 7

graph.add_edge(START, "orchestrate_queries")
graph.add_edge("orchestrate_queries", "fetch_documents")
graph.add_edge("fetch_documents", "retrieve_internal_knowledge")
graph.add_edge("retrieve_internal_knowledge", "label_sentiment_and_analyze")
graph.add_edge("label_sentiment_and_analyze", "consolidate_memory")
graph.add_edge("consolidate_memory", "theme_agents")
graph.add_edge("theme_agents", "build_snapshot")
graph.add_edge("build_snapshot", END)

compiled_graph = graph.compile()


async def generate_snapshot(
    request: SnapshotRequest,
    progress_callback=None,
) -> SnapshotResponse:
    """Generate a sentiment snapshot with optional progress callbacks.
    
    Args:
        request: The snapshot request configuration
        progress_callback: Optional async callback(stage, message, progress) for real-time updates
    """
    logger.info(
        "[snapshot] generate_snapshot invoked",
        extra={
            "platforms": request.platforms,
            "time_window": request.time_window,
            "focus_areas": request.focus_areas,
            "include_alerts": request.include_alerts,
        },
    )
    
    # Define progress stages with their weights
    stages = [
        ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
        ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.25),
        ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.35),
        ("analyze", "⚡ Analyzing: Unified Sentiment + Credibility...", 0.55),
        ("memory", "💾 Memory: Consolidating new knowledge...", 0.70),
        ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
    ]
    
    state: SnapshotState = {"request": request}
    
    # Run each node manually to emit progress
    try:
        # Stage 1: Query Orchestrator
        if progress_callback:
            await progress_callback("query_orchestrator", stages[0][1], stages[0][2])
        state = await orchestrate_queries(state)
        
        # Stage 2: External Retrieval
        if progress_callback:
            await progress_callback("retrieval", stages[1][1], stages[1][2])
        state = await fetch_documents(state)
        
        # Stage 3: Internal Retrieval (Recall)
        if progress_callback:
            await progress_callback("recall", stages[2][1], stages[2][2])
        state = await retrieve_internal_knowledge(state)
        
        ext_count = len(state.get("external_documents", []))
        int_count = len(state.get("internal_documents", []))
        
        # Stage 4: Unified Analysis
        if progress_callback:
            msg = f"⚡ Analyzing {ext_count} fresh + {int_count} memory docs..."
            await progress_callback("analyze", msg, stages[3][2])
        state = await label_sentiment_and_analyze(state)
        
        # Stage 5: Memory Consolidation
        if progress_callback:
            await progress_callback("memory", stages[4][1], stages[4][2])
        state = await consolidate_memory(state)
        
        # Stage 6: Theme Agents
        if progress_callback:
            await progress_callback("themes", stages[5][1], stages[5][2])
        state = theme_agents(state)
        
        # Final: Build Snapshot
        state = await build_snapshot(state)
        
    except Exception as exc:
        logger.exception("[snapshot] Pipeline failed: %s", exc)
        raise
    
    snapshot = state.get("snapshot")
    if snapshot is None:
        return SnapshotResponse(
            overall_sentiment=SentimentBreakdown(
                label="No Data",
                summary="No recent documents were available for the selected configuration.",
                scores={"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            ),
            actionable_insights=[],
            alerts=None,
            sources=[],
        )
    return snapshot
