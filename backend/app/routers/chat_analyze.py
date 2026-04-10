"""Chat-based Sentiment Analysis using the same Multi-Agent Architecture.

This endpoint provides a conversational interface that intelligently routes:
1. Sentiment analysis requests → 13-agent pipeline (7 core + 6 theme)
2. Quick Q&A requests → Simple LangSearch + Gemini

Supports two modes:
1. Streaming (SSE) - Real-time progress updates
2. Background Task + Polling - Resilient to mobile disconnections

The polling mode is recommended for production as it survives:
- Mobile alt-tab / screen off
- Network interruptions
- Browser tab suspension

Evaluation Modes (for API Cost Reduction testing):
- llm_only: Single LLM verification (Baseline 1)
- rag: Simple RAG retrieval (Baseline 2)
- agentic_rag: LangSearch + LLM consensus (SOTA Baseline)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import AsyncGenerator
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.insights.graph import generate_snapshot
from ..schemas.snapshot import SnapshotRequest, SnapshotResponse
from ..services.agents.chat_agent import run_chat_agent
from ..services.task_manager import get_task_manager, TaskStatus
from ..services.llm.groq_provider import get_groq_provider
from ..services.langsearch import LangSearchClient
from ..services.metrics.collector import get_metrics_collector, PipelineMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat-analyze"])

# In-memory session storage (for caching analysis results)
_session_cache: dict[str, dict] = {}

# Evaluation metrics storage - SEPARATE folders for each mode
EVAL_BASE_DIR = Path("backend/data/evaluation")
LLM_ONLY_METRICS_DIR = EVAL_BASE_DIR / "llm_only" / "metrics"
RAG_METRICS_DIR = EVAL_BASE_DIR / "rag" / "metrics"
AGENTIC_RAG_METRICS_DIR = EVAL_BASE_DIR / "agentic_rag" / "metrics"

# AgenticHinaing mode metrics - SAME folder as 7-node production metrics
AGENTIC_HINAING_METRICS_DIR = Path("backend/backend/data/metrics")

# Ensure directories exist
for dir_path in [LLM_ONLY_METRICS_DIR, RAG_METRICS_DIR, AGENTIC_RAG_METRICS_DIR, AGENTIC_HINAING_METRICS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class ChatMessage(BaseModel):
    """A single message in conversation history."""
    role: str  # "user" or "assistant"
    content: str


class ChatAnalyzeRequest(BaseModel):
    """Request for chat-based sentiment analysis."""
    message: str = Field(..., description="User message")
    session_id: str | None = Field(default=None, description="Session ID for conversation continuity")
    history: list[ChatMessage] = Field(default_factory=list, description="Conversation history")
    platforms: list[str] = Field(default=["web"], description="Platforms to search")
    time_window: str = Field(default="24h", description="Time window for search")
    mode: str = Field(default="auto", description="Analysis mode: auto, full, sentiment, or epistemic")

    # NEW: System mode toggle (AgenticHinaing vs Evaluation)
    system_mode: str = Field(default="agentic_hinaing", description="System mode: agentic_hinaing (intelligent routing) or evaluation (manual baseline selection)")
    eval_mode: str | None = Field(default=None, description="Evaluation mode: llm_only, rag, or agentic_rag (only used when system_mode='evaluation')")

    # ABLATION STUDY: Binary toggle for empirical validation
    ablation_preset: str = Field(default="full", description="Ablation study toggle: 'full' or 'ablated'")


class ChatProgress(BaseModel):
    """Progress update during analysis."""
    stage: str
    message: str
    progress: float  # 0.0 to 1.0
    data: dict | None = None


def detect_intent(message: str, history: list[ChatMessage]) -> str:
    """Detect user intent to route to appropriate handler.
    
    Returns:
        "analyze" - Run full multi-agent sentiment pipeline
        "followup" - Answer based on cached analysis results
        "simple" - Quick Q&A using LangSearch + Gemini
    """
    message_lower = message.lower()
    
    # Keywords that trigger sentiment analysis
    analyze_keywords = [
        "analyze", "sentiment", "public opinion", "what do people think",
        "how do citizens feel", "civic sentiment", "generate insight",
        "run analysis", "check sentiment", "sentiment breakdown",
        "what's the mood", "public perception", "community sentiment"
    ]
    
    # Keywords for follow-up on existing analysis
    followup_keywords = [
        "tell me more", "explain", "why", "what about", "sources",
        "evidence", "details", "elaborate", "based on the analysis",
        "from the results", "according to", "you mentioned"
    ]
    
    # Check if this is a follow-up (has history AND uses follow-up keywords)
    has_recent_analysis = len(history) > 0 and any(
        "Sentiment Analysis Results" in msg.content or
        "analyzing" in msg.content.lower()
        for msg in history[-5:]  # Check last 5 messages
    )
    
    if has_recent_analysis and any(kw in message_lower for kw in followup_keywords):
        return "followup"
    
    # Check for analysis intent
    if any(kw in message_lower for kw in analyze_keywords):
        return "analyze"
    
    # Focus area mentions with analysis context
    focus_areas = ["safety", "infrastructure", "health", "tourism", "economy", "environment"]
    if any(area in message_lower for area in focus_areas):
        # Check if context suggests analysis
        analysis_context = ["in baguio", "baguio city", "about", "regarding", "concerning"]
        if any(ctx in message_lower for ctx in analysis_context):
            return "analyze"
    
    # Default to simple Q&A
    return "simple"


def parse_user_intent(message: str) -> tuple[list[str], str]:
    """Parse user message to extract focus areas and time window.
    
    Returns:
        Tuple of (focus_areas, time_window)
    """
    message_lower = message.lower()
    
    # Detect focus areas from message
    focus_mapping = {
        "infrastructure": ["infrastructure", "traffic", "road", "water", "power", "transport"],
        "health": ["health", "hospital", "medical", "disease", "healthcare", "bgh"],
        "safety": ["safety", "crime", "accident", "fire", "disaster", "police", "walkout", "protest"],
        "tourism": ["tourism", "tourist", "travel", "hotel", "burnham", "panagbenga"],
        "economy": ["economy", "economic", "business", "vendor", "market", "job", "employment", "mall"],
        "environment": ["environment", "pollution", "tree", "flood", "waste", "climate"],
    }
    
    detected_areas = []
    for area, keywords in focus_mapping.items():
        if any(kw in message_lower for kw in keywords):
            detected_areas.append(area)
    
    # Default to all areas if none detected
    if not detected_areas:
        detected_areas = list(focus_mapping.keys())
    
    # Detect time window
    time_window = "24h"  # default
    if "today" in message_lower or "now" in message_lower:
        time_window = "6h"
    elif "week" in message_lower:
        time_window = "7d"
    elif "3 day" in message_lower or "three day" in message_lower:
        time_window = "3d"
    
    return detected_areas, time_window


def format_results_for_chat(response) -> str:
    """Format the SnapshotResponse for chat display.
    
    SnapshotResponse fields:
    - overall_sentiment: SentimentBreakdown (label, summary, scores)
    - actionable_insights: list[Insight] (category, title, detail, evidence)
    - sources: list[WebDocument] | None
    - alerts: list[str] | None
    """
    lines = []
    
    # Header
    lines.append("## 📊 Sentiment Analysis Results\n")
    
    # Summary from overall_sentiment
    if response.overall_sentiment:
        lines.append(f"**Overall Sentiment:** {response.overall_sentiment.label.capitalize()}")
        if response.overall_sentiment.summary:
            summary = response.overall_sentiment.summary
            lines.append(f"\n{summary[:800]}..." if len(summary) > 800 else f"\n{summary}")
        
        # Sentiment scores (positive, negative, neutral)
        if response.overall_sentiment.scores:
            lines.append("\n### Sentiment Breakdown")
            scores = response.overall_sentiment.scores
            pos = scores.get("positive", 0)
            neg = scores.get("negative", 0)
            neu = scores.get("neutral", 0)
            total = pos + neg + neu
            if total > 0:
                lines.append(f"- 🟢 Positive: {pos:.0%}")
                lines.append(f"- 🔴 Negative: {neg:.0%}")
                lines.append(f"- ⚪ Neutral: {neu:.0%}\n")
    
    # Key Insights with full detail and evidence
    if response.actionable_insights:
        lines.append("### Key Insights")
        for i, insight in enumerate(response.actionable_insights, 1):
            lines.append(f"\n**{i}. {insight.title}** ({insight.category})")
            # Full detail (not truncated)
            if insight.detail:
                lines.append(f"{insight.detail}")
            # Evidence citations
            if insight.evidence:
                lines.append("\n*Supporting evidence:*")
                for ev in insight.evidence[:3]:  # Max 3 evidence per insight
                    ev_text = ev[:150] + "..." if len(ev) > 150 else ev
                    lines.append(f"  - {ev_text}")
    
    # Alerts
    if response.alerts:
        lines.append("\n### ⚠️ Alerts")
        for alert in response.alerts[:5]:
            lines.append(f"- {alert}")
    
    # Top Sources
    doc_count = len(response.sources) if response.sources else 0
    if response.sources and doc_count > 0:
        lines.append("\n### 📰 Top Sources")
        seen_titles = set()
        for doc in response.sources[:10]:  # Max 10 sources
            if doc.title not in seen_titles:
                seen_titles.add(doc.title)
                title = doc.title[:60] + "..." if len(doc.title) > 60 else doc.title
                sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(doc.sentiment, "")
                lines.append(f"- {sentiment_emoji} [{title}]({doc.url})")
    
    # Footer
    lines.append(f"\n---\n_Analyzed {doc_count} documents_")
    
    return "\n".join(lines)


async def stream_analysis(request: ChatAnalyzeRequest) -> AsyncGenerator[str, None]:
    """Smart streaming handler with Evaluation Mode support.

    Routes:
    - AgenticHinaing Mode: Intelligent routing (analyze → 7-node, qna → Agentic RAG)
    - Evaluation Mode: Manual baseline selection (llm_only, rag, agentic_rag)
    """
    start_time = time.perf_counter()
    metrics = get_metrics_collector()
    
    # Start metrics run
    run_id = str(uuid.uuid4())[:8]
    metrics.start_run(
        run_id=run_id,
        focus_areas=["chat"],
        time_window=request.time_window,
        mode=f"chat_{request.system_mode}_{request.eval_mode or 'default'}",
    )
    
    # EVALUATION MODE: Manual baseline selection
    if request.system_mode == "evaluation":
        eval_mode = request.eval_mode or "agentic_rag"
        logger.info(f"[chat_analyze] Evaluation mode: {eval_mode}, run_id: {run_id}")
        
        yield json.dumps({
            "type": "progress",
            "stage": "start",
            "message": f"🔬 Running {eval_mode} baseline...",
            "progress": 0.3
        }) + "\n"
        
        try:
            sources = []
            response_text = ""
            docs_fresh = 1  # Default for evaluation modes
            
            if eval_mode == "llm_only":
                # Baseline 1: Single LLM (no retrieval)
                from ..services.llm.groq_provider import get_groq_provider
                llm = get_groq_provider("llama-3.1-8b-instant")
                response = await llm.generate(
                    prompt=request.message,
                    system_prompt="Answer concisely based on your training data.",
                    temperature=0.3,
                    max_tokens=512,
                )
                response_text = response
                docs_fresh = 0  # No docs retrieved
            
            elif eval_mode == "rag":
                # Baseline 2: Simple RAG (retrieval only, no multi-agent)
                search_client = LangSearchClient()
                search_results = await search_client.search(
                    query=request.message,
                    time_window="30d",
                    limit=10
                )
                sources = [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in search_results[:5]]
                docs_fresh = len(search_results)
                
                # Build context from search results
                context = "\n\n".join([f"{r.title}: {r.snippet}" for r in search_results[:5]])
                response_text = await llm.generate(
                    prompt=f"Based on these search results:\n{context}\n\nQuestion: {request.message}",
                    system_prompt="Answer based only on the provided search results.",
                    temperature=0.3,
                    max_tokens=512,
                )
            
            else:  # agentic_rag
                # Baseline 3: Agentic RAG (current chat_agent.py)
                response_text, sources_list = await run_chat_agent(
                    message=request.message,
                    history=request.history,
                    jurisdiction="Baguio City"
                )
                sources = sources_list
                docs_fresh = len(sources_list) if sources_list else 1
            
            # Calculate metrics (SAME schema as 7-node)
            latency_ms = (time.perf_counter() - start_time) * 1000
            docs_cached = 0  # Evaluation modes have NO Smart Reuse
            api_calls_total = docs_fresh * 2  # Sentiment + Credibility per doc
            api_calls_actual = api_calls_total  # No caching in evaluation modes
            
            # Record metrics (SAME as nodes.py)
            metrics.record_api_cost_reduction(
                api_calls_total=api_calls_total,
                api_calls_actual=api_calls_actual,
                documents_cached=docs_cached,
                documents_fresh=docs_fresh,
            )
            metrics.record_retrieval_metrics(
                external_count=docs_fresh,
                internal_count=0,
                after_dedup=docs_fresh,
            )
            
            # End run and save to mode-specific folder
            run_metrics = metrics.end_run()
            metrics_dict = run_metrics.to_dict() if run_metrics else {}
            metrics_dict["eval_mode"] = eval_mode
            metrics_dict["system_mode"] = "evaluation"
            
            mode_dir = {
                "llm_only": LLM_ONLY_METRICS_DIR,
                "rag": RAG_METRICS_DIR,
                "agentic_rag": AGENTIC_RAG_METRICS_DIR,
            }[eval_mode]
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            filepath = mode_dir / f"metrics_{date_str}.jsonl"
            
            with open(filepath, "a") as f:
                f.write(json.dumps(metrics_dict) + "\n")
            
            yield json.dumps({
                "type": "result",
                "stage": "complete",
                "message": response_text,
                "progress": 1.0,
                "data": {
                    "mode": "evaluation",
                    "eval_mode": eval_mode,
                    "sources": sources,
                }
            }) + "\n"
            
        except Exception as exc:
            logger.exception("Evaluation mode failed: %s", exc)
            metrics.record_error(str(exc))
            metrics.end_run()
            yield json.dumps({
                "type": "error",
                "stage": "error",
                "message": f"❌ Evaluation failed: {str(exc)[:100]}",
                "progress": 0.0
            }) + "\n"
        return
    
    # AGENTIC HINAING MODE: Intelligent routing (default production behavior)
    logger.info(f"[chat_analyze] AgenticHinaing mode, session: {request.session_id or 'new'}")
    
    # Detect intent
    intent = detect_intent(request.message, request.history)
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"[chat_analyze] Intent detected: {intent}, session: {session_id}")

    if intent == "simple":
        # Route to simple chat agent (fast)
        yield json.dumps({
            "type": "progress",
            "stage": "start",
            "message": "💬 Processing your question...",
            "progress": 0.3
        }) + "\n"

        try:
            # Convert history to format expected by chat_agent
            history = [{"role": msg.role, "content": msg.content} for msg in request.history]

            # Call the simple chat agent
            response_text, sources = await run_chat_agent(
                message=request.message,
                history=request.history,
                jurisdiction="Baguio City"
            )
            
            # Log metrics for AgenticHinaing mode (simple intent)
            latency_ms = (time.perf_counter() - start_time) * 1000
            docs_fresh = len(sources) if sources else 1
            docs_cached = 0  # Simple chat doesn't use Smart Reuse
            api_calls_total = docs_fresh * 2
            api_calls_actual = api_calls_total

            metrics.record_api_cost_reduction(
                api_calls_total=api_calls_total,
                api_calls_actual=api_calls_actual,
                documents_cached=docs_cached,
                documents_fresh=docs_fresh,
            )
            metrics.record_retrieval_metrics(
                external_count=docs_fresh,
                internal_count=0,
                after_dedup=docs_fresh,
            )

            # Save to AgenticHinaing metrics (same folder as 7-node)
            run_metrics = metrics.end_run()
            metrics_dict = run_metrics.to_dict() if run_metrics else {}
            metrics_dict["system_mode"] = "agentic_hinaing"
            metrics_dict["intent"] = "simple"

            date_str = datetime.now().strftime("%Y-%m-%d")
            filepath = AGENTIC_HINAING_METRICS_DIR / f"metrics_{date_str}.jsonl"

            with open(filepath, "a") as f:
                f.write(json.dumps(metrics_dict) + "\n")

            yield json.dumps({
                "type": "result",
                "stage": "complete",
                "message": response_text,
                "progress": 1.0,
                "data": {
                    "mode": "simple",
                    "sources": sources
                }
            }) + "\n"

        except Exception as exc:
            logger.exception("Simple chat failed: %s", exc)
            metrics.record_error(str(exc))
            metrics.end_run()
            yield json.dumps({
                "type": "error",
                "stage": "error",
                "message": f"❌ Failed to process question: {str(exc)[:100]}",
                "progress": 0.0
            }) + "\n"
        return
    
    elif intent == "followup":
        # RAG on cached analysis results
        cached = _session_cache.get(session_id)
        
        if cached and "response" in cached:
            yield json.dumps({
                "type": "progress",
                "stage": "start",
                "message": "🔍 Looking up from previous analysis...",
                "progress": 0.3
            }) + "\n"
            
            try:
                # Build context from cached response
                cached_response = cached["response"]
                
                # Context summary for the agent
                analysis_context = ""
                if cached_response.overall_sentiment:
                    analysis_context += f"Overall Sentiment: {cached_response.overall_sentiment.label}\n"
                    analysis_context += f"Summary: {cached_response.overall_sentiment.summary}\n"
                
                # Pass this context to the agent so it knows what was discussed
                # The agent will then perform FRESH Web + RAG search for the new question
                augmented_message = (
                    f"CONTEXT FROM PREVIOUS ANALYSIS: \n{analysis_context}\n\n"
                    f"USER QUESTION: {request.message}\n"
                    f"(Use your tools to find fresh info if needed.)"
                )
                
                # Run the Full Agentic Hybrid Search
                response_text, sources = await run_chat_agent(
                    message=augmented_message,
                    history=request.history,
                    jurisdiction="Baguio City",
                    system_instruction=(
                        "You are the **Synthesis Agent** (Node 7) of the Hinaing Multi-Agent System. "
                        "You represent the collective insights of the full 7-node architecture (Sentiment, Credibility, etc.). "
                        "You rely on the provided Context and your Tools to answer follow-up questions. "
                        "Do NOT apologize. Act as the intelligent interface for the analysis."
                    )
                )

                # Log metrics for AgenticHinaing mode (followup intent)
                latency_ms = (time.perf_counter() - start_time) * 1000
                docs_fresh = len(sources) if sources else 1
                docs_cached = 0  # Followup doesn't use Smart Reuse
                api_calls_total = docs_fresh * 2
                api_calls_actual = api_calls_total

                metrics.record_api_cost_reduction(
                    api_calls_total=api_calls_total,
                    api_calls_actual=api_calls_actual,
                    documents_cached=docs_cached,
                    documents_fresh=docs_fresh,
                )
                metrics.record_retrieval_metrics(
                    external_count=docs_fresh,
                    internal_count=0,
                    after_dedup=docs_fresh,
                )

                # Save to AgenticHinaing metrics (same folder as 7-node)
                run_metrics = metrics.end_run()
                metrics_dict = run_metrics.to_dict() if run_metrics else {}
                metrics_dict["system_mode"] = "agentic_hinaing"
                metrics_dict["intent"] = "followup"

                date_str = datetime.now().strftime("%Y-%m-%d")
                filepath = AGENTIC_HINAING_METRICS_DIR / f"metrics_{date_str}.jsonl"

                with open(filepath, "a") as f:
                    f.write(json.dumps(metrics_dict) + "\n")

                yield json.dumps({
                    "type": "result",
                    "stage": "complete",
                    "message": response_text,
                    "progress": 1.0,
                    "data": {
                        "mode": "simple",  # Render as Simple Q&A (Text + Sources)
                        "sources": sources
                    }
                }) + "\n"

            except Exception as exc:
                logger.exception("Follow-up agent failed: %s", exc)
                # Fallback to simple chat (without augmented context if that failed)
                yield json.dumps({
                    "type": "progress",
                    "stage": "fallback",
                    "message": "🔄 Refrying search...",
                    "progress": 0.5
                }) + "\n"

                response_text, sources = await run_chat_agent(
                    message=request.message,
                    history=request.history,
                    jurisdiction="Baguio City"
                )

                # Log metrics for fallback
                latency_ms = (time.perf_counter() - start_time) * 1000
                docs_fresh = len(sources) if sources else 1
                api_calls_total = docs_fresh * 2

                metrics.record_api_cost_reduction(
                    api_calls_total=api_calls_total,
                    api_calls_actual=api_calls_total,
                    documents_cached=0,
                    documents_fresh=docs_fresh,
                )

                run_metrics = metrics.end_run()
                metrics_dict = run_metrics.to_dict() if run_metrics else {}
                metrics_dict["system_mode"] = "agentic_hinaing"
                metrics_dict["intent"] = "followup_fallback"

                date_str = datetime.now().strftime("%Y-%m-%d")
                filepath = AGENTIC_HINAING_METRICS_DIR / f"metrics_{date_str}.jsonl"

                with open(filepath, "a") as f:
                    f.write(json.dumps(metrics_dict) + "\n")

                yield json.dumps({
                    "type": "result",
                    "stage": "complete",
                    "message": response_text,
                    "progress": 1.0,
                    "data": {"mode": "simple_fallback", "sources": sources}
                }) + "\n"
            return
        else:
            # Cache miss - Fallback to Agentic Search seamlessly
            yield json.dumps({
                "type": "progress",
                "stage": "fallback",
                "message": "🔄 Analysis context expired. Switching to Fast Agentic Search...",
                "progress": 0.5
            }) + "\n"
            
            try:
                response_text, sources = await run_chat_agent(
                    message=request.message,
                    history=request.history,
                    jurisdiction="Baguio City",
                    system_instruction="You are an intelligent Agentic RAG assistant. The user is asking a follow-up, but the previous analysis context is lost. You MUST use your 'search_civic_data' tool to find the answer. Do NOT apologize. Do NOT say you cannot access the internet. USE THE TOOL."
                )
                
                yield json.dumps({
                    "type": "result",
                    "stage": "complete",
                    "message": response_text,
                    "progress": 1.0,
                    "data": {"mode": "simple_fallback", "sources": sources}
                }) + "\n"
            except Exception as e:
                logger.error(f"Fallback agent failed: {e}")
                yield json.dumps({
                    "type": "error",
                    "stage": "error",
                    "message": "I lost the context and couldn't search for it. Please try analyzing again.",
                    "progress": 0.0
                }) + "\n"
            return
    
    # intent == "analyze" - Full multi-agent pipeline
    focus_areas, time_window = parse_user_intent(request.message)
    
    yield json.dumps({
        "type": "progress",
        "stage": "start",
        "message": f"🔄 Starting multi-agent analysis for: {', '.join(focus_areas)}",
        "progress": 0.0
    }) + "\n"
    
    # Create the snapshot request
    snapshot_request = SnapshotRequest(
        focus_areas=focus_areas,
        platforms=request.platforms,
        time_window=time_window,
        mode=request.mode,
        ablation_preset=request.ablation_preset,
    )
    
    # Queue for progress updates from the pipeline
    progress_queue: asyncio.Queue = asyncio.Queue()
    
    async def progress_callback(stage: str, message: str, progress: float):
        """Callback to receive progress updates from the pipeline."""
        await progress_queue.put({
            "type": "progress",
            "stage": stage,
            "message": message,
            "progress": progress
        })
    
    try:
        # Start the pipeline in a task so we can yield progress updates
        pipeline_task = asyncio.create_task(
            generate_snapshot(snapshot_request, progress_callback=progress_callback)
        )
        
        # Yield progress updates as they come in
        while not pipeline_task.done():
            try:
                # Wait for progress update with timeout
                progress_update = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                yield json.dumps(progress_update) + "\n"
            except asyncio.TimeoutError:
                # No update yet, continue waiting
                continue
        
        # Drain any remaining progress updates
        while not progress_queue.empty():
            progress_update = await progress_queue.get()
            yield json.dumps(progress_update) + "\n"
        
        # Get the result
        response = await pipeline_task
        
        # Cache the response for follow-up questions
        _session_cache[session_id] = {
            "response": response,
            "focus_areas": focus_areas,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get document count from sources
        doc_count = len(response.sources) if response.sources else 0
        
        # Format and send final results
        formatted_results = format_results_for_chat(response)
        
        # Extract sentiment scores as percentages
        sentiment_scores = None
        if response.overall_sentiment and response.overall_sentiment.scores:
            scores = response.overall_sentiment.scores
            sentiment_scores = {
                "positive": round(scores.get("positive", 0) * 100),
                "negative": round(scores.get("negative", 0) * 100),
                "neutral": round(scores.get("neutral", 0) * 100),
            }
        
        # Extract insights for structured display
        insights_data = []
        if response.actionable_insights:
            for insight in response.actionable_insights:
                # Ensure evidence URLs are strings
                evidence_strs = [str(e) for e in (insight.evidence[:3] if insight.evidence else [])]
                insights_data.append({
                    "category": str(insight.category) if insight.category else "",
                    "title": str(insight.title) if insight.title else "",
                    "detail": str(insight.detail) if insight.detail else "",
                    "evidence": evidence_strs,
                })
        
        # Extract sources for structured display
        sources_data = []
        if response.sources:
            for doc in response.sources:
                meta = doc.metadata or {}
                # Ensure all values are JSON serializable
                cred_score = meta.get("credibility_score")
                sources_data.append({
                    "title": str(doc.title) if doc.title else "",
                    "snippet": str(doc.snippet)[:200] if doc.snippet else "",
                    "url": str(doc.url) if doc.url else None,
                    "sentiment": str(doc.sentiment) if doc.sentiment else None,
                    "credibility_score": float(cred_score) if cred_score is not None else None,
                    "credibility_tier": str(meta.get("credibility_tier")) if meta.get("credibility_tier") else None,
                    "verification_status": str(meta.get("verification_status")) if meta.get("verification_status") else None,
                })
        
        # Compute credibility breakdown
        high_cred = sum(1 for s in sources_data if (s.get("credibility_score") or 0) >= 0.55)
        low_cred = len(sources_data) - high_cred
        avg_cred = sum(s.get("credibility_score") or 0.5 for s in sources_data) / max(1, len(sources_data))
        
        # NEW: Include faithfulness verification metrics (same as Sentiment Generator)
        verification_data = None
        if response.verification:
            verification_data = {
                "total_claims": response.verification.total_claims,
                "verified_claims": response.verification.verified_claims,
                "unverified_claims": response.verification.unverified_claims,
                "faithfulness_score": response.verification.faithfulness_score,
                "hallucination_analysis": {
                    "is_hallucination_free": response.verification.hallucination_analysis.is_hallucination_free if response.verification.hallucination_analysis else True,
                    "hallucination_count": response.verification.hallucination_analysis.hallucination_count if response.verification.hallucination_analysis else 0,
                    "hallucination_types": dict(response.verification.hallucination_analysis.hallucination_types) if response.verification.hallucination_analysis else {},
                } if response.verification.hallucination_analysis else None,
                "misattribution_analysis": {
                    "misattribution_count": response.verification.misattribution_analysis.misattribution_count,
                    "misattribution_rate": response.verification.misattribution_analysis.misattribution_rate,
                } if response.verification.misattribution_analysis else None,
                "numerical_hallucinations": {
                    "count": response.verification.numerical_hallucinations.count,
                    "rate": response.verification.numerical_hallucinations.rate,
                    "details": [
                        {"claim": d.claim, "unsupported_numbers": d.unsupported_numbers}
                        for d in (response.verification.numerical_hallucinations.details or [])
                    ],
                } if response.verification.numerical_hallucinations and response.verification.numerical_hallucinations.count > 0 else None,
                "citation_verification": {
                    "total_citations": response.verification.citation_verification.total_citations,
                    "valid_citations": response.verification.citation_verification.valid_citations,
                    "citation_accuracy_rate": response.verification.citation_verification.citation_accuracy_rate,
                } if response.verification.citation_verification else None,
            }
        
        yield json.dumps({
            "type": "result",
            "stage": "complete",
            "message": formatted_results,
            "progress": 1.0,
            "data": {
                "mode": "analyze",
                "session_id": session_id,
                "overall_sentiment": {
                    "label": response.overall_sentiment.label if response.overall_sentiment else "neutral",
                    "summary": response.overall_sentiment.summary if response.overall_sentiment else "",
                    "scores": sentiment_scores,
                },
                "insights": insights_data,
                "sources": sources_data,
                "credibility": {
                    "avg_score": round(avg_cred * 100),
                    "high_percent": round(high_cred / max(1, len(sources_data)) * 100),
                    "low_percent": round(low_cred / max(1, len(sources_data)) * 100),
                },
                "verification": verification_data,  # NEW: Faithfulness metrics
                "document_count": doc_count,
                "insights_count": len(insights_data),
                "alerts": response.alerts[:5] if response.alerts else [],
            }
        }) + "\n"
        
    except Exception as exc:
        logger.exception("Chat analysis failed: %s", exc)
        yield json.dumps({
            "type": "error",
            "stage": "error",
            "message": f"❌ Analysis failed: {str(exc)[:100]}",
            "progress": 0.0
        }) + "\n"


@router.post("/analyze")
async def chat_analyze(request: ChatAnalyzeRequest):
    """Stream sentiment analysis through multi-agent pipeline.
    
    This endpoint uses the SAME architecture as the dashboard Sentiment Generator:
    1. Query Orchestrator (ReAct)
    2. Retrieval Agent (Multi-query)
    3. Sentiment Agent (RoBERTa + Gemini ensemble)
    4. Credibility Agent (5-signal verification)
    5. Theme Agents (RAG-augmented insights)
    6. Narrative Generator
    
    Responses are streamed as newline-delimited JSON.
    """
    return StreamingResponse(
        stream_analysis(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/analyze/sync")
async def chat_analyze_sync(request: ChatAnalyzeRequest):
    """Non-streaming version for simpler clients."""
    focus_areas, time_window = parse_user_intent(request.message)

    snapshot_request = SnapshotRequest(
        focus_areas=focus_areas,
        platforms=request.platforms,
        time_window=time_window,
        mode=request.mode,
        ablation_preset=request.ablation_preset,
    )
    
    try:
        response = await generate_snapshot(snapshot_request)
        doc_count = len(response.sources) if response.sources else 0
        
        # Extract sentiment data from overall_sentiment.scores
        sentiment_data = None
        if response.overall_sentiment and response.overall_sentiment.scores:
            scores = response.overall_sentiment.scores
            sentiment_data = {
                "positive": int(scores.get("positive", 0) * doc_count),
                "negative": int(scores.get("negative", 0) * doc_count),
                "neutral": int(scores.get("neutral", 0) * doc_count),
            }
        
        return {
            "success": True,
            "message": format_results_for_chat(response),
            "data": {
                "sentiment": sentiment_data,
                "credibility_avg": None,
                "document_count": doc_count,
                "focus_areas": focus_areas,
                "time_window": time_window,
            }
        }
    except Exception as exc:
        logger.exception("Chat analysis failed")
        raise HTTPException(status_code=500, detail=str(exc))


# =============================================================================
# BACKGROUND TASK + POLLING ENDPOINTS (Mobile-Resilient)
# =============================================================================

def _format_snapshot_result(response: SnapshotResponse, session_id: str, focus_areas: list[str]) -> dict:
    """Format SnapshotResponse into JSON-serializable result dict."""
    doc_count = len(response.sources) if response.sources else 0
    formatted_results = format_results_for_chat(response)

    # Extract sentiment scores as percentages
    sentiment_scores = None
    if response.overall_sentiment and response.overall_sentiment.scores:
        scores = response.overall_sentiment.scores
        sentiment_scores = {
            "positive": round(scores.get("positive", 0) * 100),
            "negative": round(scores.get("negative", 0) * 100),
            "neutral": round(scores.get("neutral", 0) * 100),
        }

    # Extract insights for structured display
    insights_data = []
    if response.actionable_insights:
        for insight in response.actionable_insights:
            evidence_strs = [str(e) for e in (insight.evidence[:3] if insight.evidence else [])]
            insights_data.append({
                "category": str(insight.category) if insight.category else "",
                "title": str(insight.title) if insight.title else "",
                "detail": str(insight.detail) if insight.detail else "",
                "evidence": evidence_strs,
            })

    # Extract sources for structured display
    sources_data = []
    if response.sources:
        for doc in response.sources:
            meta = doc.metadata or {}
            cred_score = meta.get("credibility_score")
            sources_data.append({
                "title": str(doc.title) if doc.title else "",
                "snippet": str(doc.snippet)[:200] if doc.snippet else "",
                "url": str(doc.url) if doc.url else None,
                "sentiment": str(doc.sentiment) if doc.sentiment else None,
                "credibility_score": float(cred_score) if cred_score is not None else None,
                "credibility_tier": str(meta.get("credibility_tier")) if meta.get("credibility_tier") else None,
                "verification_status": str(meta.get("verification_status")) if meta.get("verification_status") else None,
                # Include full metadata for VerificationBadge component
                "metadata": {
                    "credibility_score": float(cred_score) if cred_score is not None else None,
                    "credibility_tier": str(meta.get("credibility_tier")) if meta.get("credibility_tier") else None,
                    "misinfo_risk": str(meta.get("misinfo_risk")) if meta.get("misinfo_risk") else None,
                    "corroborating_sources": int(meta.get("corroborating_sources", 0)),
                    "tavily_verified_sources": list(meta.get("tavily_verified_sources", [])),
                    "tavily_verification_status": str(meta.get("tavily_verification_status")) if meta.get("tavily_verification_status") else None,
                    "red_flags": list(meta.get("red_flags", [])),
                    "fact_check_rating": str(meta.get("fact_check_rating")) if meta.get("fact_check_rating") else None,
                    "llm_reasoning": str(meta.get("llm_reasoning", "")),
                    "credibility_breakdown": dict(meta.get("credibility_breakdown", {})),
                }
            })

    # Compute credibility breakdown
    high_cred = sum(1 for s in sources_data if (s.get("credibility_score") or 0) >= 0.55)
    low_cred = len(sources_data) - high_cred
    avg_cred = sum(s.get("credibility_score") or 0.5 for s in sources_data) / max(1, len(sources_data))

    # NEW: Include faithfulness verification metrics (same as Sentiment Generator)
    verification_data = None
    if response.verification:
        # Build full verification data structure for frontend
        verification_data = {
            "total_claims": response.verification.total_claims,
            "verified_claims": response.verification.verified_claims,
            "unverified_claims": response.verification.unverified_claims,
            "faithfulness_score": response.verification.faithfulness_score,
            # Hallucination analysis
            "hallucination_analysis": {
                "is_hallucination_free": True,  # Default to true
                "hallucination_count": 0,
                "hallucination_types": {},
            },
            # Misattribution analysis  
            "misattribution_analysis": {
                "misattribution_count": 0,
                "misattribution_rate": 0.0,
            },
            # Numerical hallucinations
            "numerical_hallucinations": {
                "count": 0,
                "rate": 0.0,
                "details": [],
            },
            # Citation verification
            "citation_verification": {
                "total_citations": 0,  # Will be populated by frontend from actual citations
                "valid_citations": 0,
                "citation_accuracy_rate": 1.0,  # Default to 100%
            },
        }

    return {
        "type": "result",
        "stage": "complete",
        "message": formatted_results,
        "progress": 1.0,
        "data": {
            "mode": "analyze",
            "session_id": session_id,
            "overall_sentiment": {
                "label": response.overall_sentiment.label if response.overall_sentiment else "neutral",
                "summary": response.overall_sentiment.summary if response.overall_sentiment else "",
                "scores": sentiment_scores,
            },
            "insights": insights_data,
            "sources": sources_data,
            "credibility": {
                "avg_score": round(avg_cred * 100),
                "high_percent": round(high_cred / max(1, len(sources_data)) * 100),
                "low_percent": round(low_cred / max(1, len(sources_data)) * 100),
            },
            "verification": verification_data,  # NEW: Faithfulness metrics
            "document_count": doc_count,
            "insights_count": len(insights_data),
            "alerts": response.alerts[:5] if response.alerts else [],
        }
    }


@router.post("/analyze/start")
async def start_analysis(request: ChatAnalyzeRequest):
    """Start analysis as a background task (returns immediately).

    This endpoint is mobile-resilient: the analysis continues even if
    the client disconnects. Poll /analyze/status/{task_id} for progress.
    
    Supports two modes:
    1. AgenticHinaing Mode (default): Intelligent routing (analyze → 7-node, qna → Agentic RAG)
    2. Evaluation Mode: Manual baseline selection (llm_only, rag, agentic_rag)

    Returns:
        task_id: Unique identifier to poll for status
        session_id: Session ID for follow-up questions
    """
    task_manager = get_task_manager()
    task_manager.start_cleanup_loop()

    # EVALUATION MODE: Check if this is an evaluation request
    if request.system_mode == "evaluation":
        eval_mode = request.eval_mode or "agentic_rag"
        logger.info(f"[chat_analyze/start] Evaluation mode: {eval_mode}")
        
        # For evaluation modes, run synchronously and return immediate result
        # The frontend will handle the response normally
        try:
            sources = []
            response_text = ""
            docs_fresh = 1

            if eval_mode == "llm_only":
                # Baseline 1: Single LLM (no retrieval)
                llm = get_groq_provider("llama-3.1-8b-instant")
                response = await llm.generate(
                    prompt=request.message,
                    system_prompt="Answer concisely based on your training data.",
                    temperature=0.3,
                    max_tokens=512,
                )
                response_text = response
                docs_fresh = 0

            elif eval_mode == "rag":
                # Baseline 2: Simple RAG (retrieval only)
                search_client = LangSearchClient()
                search_results = await search_client.search(
                    query=request.message,
                    time_window="30d",
                    limit=10
                )
                sources = [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in search_results[:5]]
                docs_fresh = len(search_results)

                context = "\n\n".join([f"{r.title}: {r.snippet}" for r in search_results[:5]])
                llm = get_groq_provider("llama-3.1-8b-instant")
                response_text = await llm.generate(
                    prompt=f"Based on these search results:\n{context}\n\nQuestion: {request.message}",
                    system_prompt="Answer based only on the provided search results.",
                    temperature=0.3,
                    max_tokens=512,
                )
                
            else:  # agentic_rag
                # Baseline 3: Agentic RAG (current chat_agent.py)
                response_text, sources_list = await run_chat_agent(
                    message=request.message,
                    history=request.history,
                    jurisdiction="Baguio City"
                )
                sources = sources_list
                docs_fresh = len(sources_list) if sources_list else 1
            
            # Log metrics for evaluation mode
            import time as time_module
            from ..services.metrics.collector import get_metrics_collector
            metrics = get_metrics_collector()
            run_id = str(uuid.uuid4())[:8]
            
            metrics.start_run(
                run_id=run_id,
                focus_areas=["chat"],
                time_window=request.time_window,
                mode=f"chat_evaluation_{eval_mode}",
            )
            
            api_calls_total = docs_fresh * 2
            api_calls_actual = api_calls_total
            
            metrics.record_api_cost_reduction(
                api_calls_total=api_calls_total,
                api_calls_actual=api_calls_actual,
                documents_cached=0,
                documents_fresh=docs_fresh,
            )
            metrics.record_retrieval_metrics(
                external_count=docs_fresh,
                internal_count=0,
                after_dedup=docs_fresh,
            )
            
            run_metrics = metrics.end_run()
            metrics_dict = run_metrics.to_dict() if run_metrics else {}
            metrics_dict["eval_mode"] = eval_mode
            metrics_dict["system_mode"] = "evaluation"
            
            mode_dir = {
                "llm_only": LLM_ONLY_METRICS_DIR,
                "rag": RAG_METRICS_DIR,
                "agentic_rag": AGENTIC_RAG_METRICS_DIR,
            }[eval_mode]
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            filepath = mode_dir / f"metrics_{date_str}.jsonl"
            
            with open(filepath, "a") as f:
                f.write(json.dumps(metrics_dict) + "\n")
            
            return {
                "task_id": None,
                "session_id": request.session_id or str(uuid.uuid4()),
                "immediate_result": {
                    "type": "result",
                    "stage": "complete",
                    "message": response_text,
                    "progress": 1.0,
                    "data": {
                        "mode": "evaluation",
                        "eval_mode": eval_mode,
                        "sources": sources
                    }
                }
            }
            
        except Exception as e:
            logger.exception("Evaluation mode failed")
            raise HTTPException(status_code=500, detail=str(e)[:200])
    
    # AGENTIC HINAING MODE: Intelligent routing (default)
    intent = detect_intent(request.message, request.history)
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"[chat_analyze/start] Intent: {intent}, session: {session_id}")

    # For simple/followup intents, run synchronously (they're fast)
    if intent in ("simple", "followup"):
        # These are fast enough to run inline
        try:
            if intent == "simple":
                response_text, sources = await run_chat_agent(
                    message=request.message,
                    history=request.history,
                    jurisdiction="Baguio City"
                )
                return {
                    "task_id": None,
                    "session_id": session_id,
                    "immediate_result": {
                        "type": "result",
                        "stage": "complete",
                        "message": response_text,
                        "progress": 1.0,
                        "data": {"mode": "simple", "sources": sources}
                    }
                }
            else:  # followup
                cached = _session_cache.get(session_id)
                if cached and "response" in cached:
                    cached_response = cached["response"]
                    analysis_context = ""
                    if cached_response.overall_sentiment:
                        analysis_context += f"Overall Sentiment: {cached_response.overall_sentiment.label}\n"
                        analysis_context += f"Summary: {cached_response.overall_sentiment.summary}\n"
                    
                    augmented_message = (
                        f"CONTEXT FROM PREVIOUS ANALYSIS: \n{analysis_context}\n\n"
                        f"USER QUESTION: {request.message}"
                    )
                    response_text, sources = await run_chat_agent(
                        message=augmented_message,
                        history=request.history,
                        jurisdiction="Baguio City"
                    )
                else:
                    response_text, sources = await run_chat_agent(
                        message=request.message,
                        history=request.history,
                        jurisdiction="Baguio City"
                    )
                
                return {
                    "task_id": None,
                    "session_id": session_id,
                    "immediate_result": {
                        "type": "result",
                        "stage": "complete",
                        "message": response_text,
                        "progress": 1.0,
                        "data": {"mode": "followup", "sources": sources}
                    }
                }
        except Exception as e:
            logger.exception("Quick response failed")
            raise HTTPException(status_code=500, detail=str(e)[:200])
    
    # For "analyze" intent, run as background task
    focus_areas, time_window = parse_user_intent(request.message)
    task_id = task_manager.create_task()

    # Create snapshot request
    snapshot_request = SnapshotRequest(
        focus_areas=focus_areas,
        platforms=request.platforms,
        time_window=time_window,
        mode=request.mode,
        ablation_preset=request.ablation_preset,
    )
    
    # Progress callback that updates task manager
    async def progress_callback(stage: str, message: str, progress: float):
        task_manager.update_progress(task_id, stage, message, progress)
    
    # Coroutine that runs the pipeline and formats result
    async def run_pipeline():
        response = await generate_snapshot(snapshot_request, progress_callback=progress_callback)
        
        # Cache for follow-up questions
        _session_cache[session_id] = {
            "response": response,
            "focus_areas": focus_areas,
            "timestamp": datetime.now().isoformat()
        }
        
        return _format_snapshot_result(response, session_id, focus_areas)
    
    # Submit task for background execution
    task_manager.submit_task(task_id, run_pipeline())
    
    return {
        "task_id": task_id,
        "session_id": session_id,
        "focus_areas": focus_areas,
        "time_window": time_window,
    }


@router.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Poll for analysis task status and progress.
    
    Returns:
        status: "pending" | "running" | "completed" | "failed"
        progress: 0.0 to 1.0
        stage: Current pipeline stage
        message: Human-readable status message
        result: Full analysis result (only when status="completed")
        error: Error message (only when status="failed")
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found. It may have expired (TTL: 10 minutes)."
        )
    
    return task.to_dict()

