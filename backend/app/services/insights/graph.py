"""LangGraph workflow definition for Hinaing's 7-Node Insights Architecture."""

from __future__ import annotations

import logging
import os
import uuid
from langgraph.graph import END, START, StateGraph

from ...core.config import get_settings
from ...schemas.snapshot import (
    SentimentBreakdown,
    SnapshotRequest,
    SnapshotResponse,
)
from ..metrics import get_metrics_collector

# Import Definitions and Nodes from modular files
from .definitions import SnapshotState
from .nodes import (
    orchestrate_queries,
    fetch_documents,
    retrieve_internal_knowledge,
    label_sentiment_and_analyze,
    consolidate_memory,
    theme_agents,
    build_snapshot,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# LangSmith Tracing
if settings.langsmith_api_key:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    if settings.langsmith_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)


# --------------------------------------------------------------------------
# GRAPH DEFINITION (The Wiring Diagram)
# --------------------------------------------------------------------------
# This defines the topology for visualization/docs, even if we run manually for precision.

graph = StateGraph(SnapshotState)

# Add Nodes
graph.add_node("orchestrate_queries", orchestrate_queries)          # Node 1
graph.add_node("fetch_documents", fetch_documents)                  # Node 2
graph.add_node("retrieve_internal_knowledge", retrieve_internal_knowledge) # Node 3
graph.add_node("label_sentiment_and_analyze", label_sentiment_and_analyze) # Node 4
graph.add_node("consolidate_memory", consolidate_memory)            # Node 5
graph.add_node("theme_agents", theme_agents)                        # Node 6
graph.add_node("build_snapshot", build_snapshot)                    # Node 7

# Add Edges (Linear Flow)
graph.add_edge(START, "orchestrate_queries")
graph.add_edge("orchestrate_queries", "fetch_documents")
graph.add_edge("fetch_documents", "retrieve_internal_knowledge")
graph.add_edge("retrieve_internal_knowledge", "label_sentiment_and_analyze")
graph.add_edge("label_sentiment_and_analyze", "consolidate_memory")
graph.add_edge("consolidate_memory", "theme_agents")
graph.add_edge("theme_agents", "build_snapshot")
graph.add_edge("build_snapshot", END)

compiled_graph = graph.compile()


# --------------------------------------------------------------------------
# EXECUTION RUNNER (The Manual Orchestrator)
# --------------------------------------------------------------------------
# We run nodes manually to support granular Progress Callbacks and Metric Collection

async def generate_snapshot(
    request: SnapshotRequest,
    progress_callback=None,
) -> SnapshotResponse:
    """Generate a sentiment snapshot with detailed progress tracking."""

    # Initialize Request Metadata
    metrics = get_metrics_collector()
    run_id = str(uuid.uuid4())[:8]
    
    # Determine execution path based on mode
    mode = request.mode.lower()
    
    # Default: include both sentiment and credibility
    include_sentiment = True
    include_credibility = True
    
    if mode == "sentiment":
        # Full pipeline with sentiment + theme routing only (no credibility)
        execute_nodes = [1, 2, 3, 4, 5, 6, 7]
        include_sentiment = True
        include_credibility = False
        progress_stages = [
            ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
            ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.2),
            ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.3),
            ("analyze", "⚡ Analyzing: Sentiment + Theme Routing...", 0.5),
            ("memory", "💾 Memory: Consolidating new knowledge...", 0.7),
            ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
            ("snapshot", "📊 Building Snapshot Response...", 1.0),
        ]
    elif mode == "credibility":
        # Full pipeline with credibility + theme routing only (no sentiment)
        execute_nodes = [1, 2, 3, 4, 5, 6, 7]
        include_sentiment = False
        include_credibility = True
        progress_stages = [
            ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
            ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.2),
            ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.3),
            ("analyze", "⚡ Analyzing: Credibility + Theme Routing...", 0.5),
            ("memory", "💾 Memory: Consolidating new knowledge...", 0.7),
            ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
            ("snapshot", "📊 Building Snapshot Response...", 1.0),
        ]
    else:
        # Full analysis: all nodes with both sentiment and credibility
        execute_nodes = [1, 2, 3, 4, 5, 6, 7]
        include_sentiment = True
        include_credibility = True
        progress_stages = [
            ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
            ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.2),
            ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.3),
            ("analyze", "⚡ Analyzing: Sentiment + Credibility + Theme...", 0.5),
            ("memory", "💾 Memory: Consolidating new knowledge...", 0.7),
            ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
            ("snapshot", "📊 Building Snapshot Response...", 1.0),
        ]
    
    # Start metrics with mode tracking
    metrics.start_run(
        run_id=run_id,
        focus_areas=request.focus_areas or [],
        time_window=request.time_window or "24h",
        mode=mode,
        sentiment_skipped=not include_sentiment,
        credibility_skipped=not include_credibility,
    )
    
    state: SnapshotState = {
        "request": request,
        "include_sentiment": include_sentiment,
        "include_credibility": include_credibility,
    }

    try:
        # NODE 1: Query Orchestrator (always executed)
        if 1 in execute_nodes:
            if progress_callback:
                await progress_callback("query_orchestrator", progress_stages[0][1], progress_stages[0][2])
            metrics.start_timer("query_orchestrator")
            state = await orchestrate_queries(state)
            metrics.stop_timer("query_orchestrator")

            # Metrics: Query
            plan = state.get("retrieval_plan")
            if plan:
                metrics.record_query_metrics(len(plan.queries), plan.strategy[:50])

        # NODE 2: External Retrieval (always executed)
        if 2 in execute_nodes:
            if progress_callback:
                await progress_callback("retrieval", progress_stages[1][1], progress_stages[1][2])
            metrics.start_timer("external_retrieval")
            state = await fetch_documents(state)
            metrics.stop_timer("external_retrieval")

        # NODE 3: Internal Retrieval (always executed)
        if 3 in execute_nodes:
            if progress_callback:
                await progress_callback("recall", progress_stages[2][1], progress_stages[2][2])
            metrics.start_timer("internal_retrieval")
            state = await retrieve_internal_knowledge(state)
            metrics.stop_timer("internal_retrieval")

            # Metrics: Retrieval
            ext_count = len(state.get("external_documents", []))
            int_count = len(state.get("internal_documents", []))
            dedup_count = len(state.get("documents", []))
            metrics.record_retrieval_metrics(ext_count, int_count, dedup_count)

        # NODE 4: Unified Analysis (sentiment mode only)
        if 4 in execute_nodes:
            if progress_callback:
                msg = f"⚡ Analyzing {ext_count} fresh + {int_count} memory docs..."
                await progress_callback("analyze", msg, progress_stages[3][2])
            # Note: 'sentiment' timer is managed inside label_sentiment_and_analyze for granular parallel tracking
            state = await label_sentiment_and_analyze(state)

            # Metrics: Analysis Results
            enriched = state.get("enriched", [])
            if enriched:
                pos = sum(1 for d in enriched if d.sentiment == "positive")
                neg = sum(1 for d in enriched if d.sentiment == "negative")
                neu = sum(1 for d in enriched if d.sentiment == "neutral")
                agreement = sum(
                    1 for d in enriched
                    if (d.metadata or {}).get("model_agreement") == "full_agreement"
                ) / max(len(enriched), 1)
                metrics.record_sentiment_metrics(pos, neg, neu, agreement)

                cred_scores = [(d.metadata or {}).get("credibility_score", 0.5) for d in enriched]
                avg_cred = sum(cred_scores) / max(len(cred_scores), 1)
                high_cred = sum(1 for s in cred_scores if s >= 0.55)
                low_cred = sum(1 for s in cred_scores if s < 0.55)
                metrics.record_credibility_metrics(avg_cred, high_cred, low_cred)

            theme_docs = state.get("theme_documents", {})
            metrics.record_theme_metrics({k: len(v) for k, v in theme_docs.items()})

        # NODE 5: Memory Consolidation
        if 5 in execute_nodes:
            if progress_callback:
                await progress_callback("memory", progress_stages[4][1], progress_stages[4][2])
            metrics.start_timer("memory_consolidation")
            state = await consolidate_memory(state)
            metrics.stop_timer("memory_consolidation")

            # Metrics: RAG
            rag_stored = state.get("rag_chunks_stored", 0)
            relevance_scores = state.get("rag_relevance_scores", [])
            avg_relevance = sum(relevance_scores) / max(len(relevance_scores), 1)
            metrics.record_rag_metrics(
                chunks_retrieved=len(state.get("internal_documents", [])),
                avg_relevance=avg_relevance,
                chunks_stored=rag_stored
            )

        # NODE 6: Theme Agents
        if 6 in execute_nodes:
            if progress_callback:
                await progress_callback("themes", progress_stages[5][1], progress_stages[5][2])
            metrics.start_timer("theme_agents")
            state = theme_agents(state)
            metrics.stop_timer("theme_agents")

        # NODE 7: Build Snapshot
        if 7 in execute_nodes:
            metrics.start_timer("coordinator")
            state = await build_snapshot(state)
            metrics.stop_timer("coordinator")

            # Metrics: Output
            snapshot = state.get("snapshot")
            if snapshot:
                insights_with_evidence = sum(1 for i in snapshot.actionable_insights if i.evidence)
                metrics.record_output_metrics(
                    len(snapshot.actionable_insights),
                    insights_with_evidence,
                    len(snapshot.alerts or [])
                )

    except Exception as exc:
        logger.exception("[snapshot] Pipeline failed: %s", exc)
        metrics.record_error(str(exc)[:100])
        metrics.end_run()
        raise

    metrics.end_run()

    snapshot = state.get("snapshot")
    if snapshot is None:
        return SnapshotResponse(
            overall_sentiment=SentimentBreakdown(
                label="No Data",
                summary="No recent documents were available.",
                scores={"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            ),
            actionable_insights=[],
            alerts=None,
            sources=[],
        )
    return snapshot
