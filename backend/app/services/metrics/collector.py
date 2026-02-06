"""Metrics collection for thesis evaluation.

Collects performance and quality metrics across the multi-agent pipeline
for academic evaluation and comparison studies.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Metrics for a single pipeline execution."""
    
    # Identification
    run_id: str = ""
    timestamp: str = ""
    focus_areas: list[str] = field(default_factory=list)
    time_window: str = ""
    
    # Latency (milliseconds)
    total_latency_ms: float = 0.0
    query_orchestrator_ms: float = 0.0
    external_retrieval_ms: float = 0.0
    internal_retrieval_ms: float = 0.0
    sentiment_analysis_ms: float = 0.0
    credibility_analysis_ms: float = 0.0
    theme_routing_ms: float = 0.0
    memory_consolidation_ms: float = 0.0
    theme_agents_ms: float = 0.0
    coordinator_ms: float = 0.0
    
    # Document counts
    external_docs_count: int = 0
    internal_docs_count: int = 0
    total_docs_count: int = 0
    docs_after_dedup: int = 0
    
    # Query metrics
    queries_generated: int = 0
    query_strategy: str = ""
    
    # Sentiment distribution
    sentiment_positive: int = 0
    sentiment_negative: int = 0
    sentiment_neutral: int = 0
    sentiment_agreement_rate: float = 0.0  # RoBERTa-Gemini agreement
    
    # Credibility metrics
    avg_credibility_score: float = 0.0
    high_credibility_count: int = 0
    low_credibility_count: int = 0
    
    # Theme routing
    themes_with_docs: int = 0
    theme_distribution: dict[str, int] = field(default_factory=dict)
    
    # RAG metrics
    rag_chunks_retrieved: int = 0
    rag_avg_relevance: float = 0.0
    memory_chunks_stored: int = 0
    
    # Output quality
    insights_generated: int = 0
    insights_with_evidence: int = 0
    alerts_triggered: int = 0
    
    # Errors
    errors: list[str] = field(default_factory=list)
    fallbacks_used: list[str] = field(default_factory=list)
    
    # Scientific evaluation metrics
    ground_truth_accuracy: float = 0.0  # If ground truth available
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    # Ablation flags (which components were enabled)
    ablation_config: dict[str, bool] = field(default_factory=lambda: {
        "query_orchestrator": True,
        "memory_recall": True,
        "memory_consolidation": True,
        "roberta_sentiment": True,
        "gemini_sentiment": True,
        "credibility_agent": True,
        "theme_agents": True,
    })
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class MetricsCollector:
    """Singleton metrics collector for pipeline evaluation."""
    
    _instance: "MetricsCollector | None" = None
    
    def __new__(cls) -> "MetricsCollector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._current_run: PipelineMetrics | None = None
        self._completed_runs: list[PipelineMetrics] = []
        self._timers: dict[str, float] = {}
        self._max_history = 100  # Keep last 100 runs in memory
        self._initialized = True
        
        # File path for persistent storage
        self._metrics_dir = Path("backend/data/metrics")
        self._metrics_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("[metrics] MetricsCollector initialized")
    
    def start_run(
        self,
        run_id: str,
        focus_areas: list[str],
        time_window: str,
        mode: str = "full",
        sentiment_skipped: bool = False,
        credibility_skipped: bool = False,
    ) -> None:
        """Start collecting metrics for a new pipeline run."""
        self._current_run = PipelineMetrics(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            focus_areas=focus_areas,
            time_window=time_window,
        )
        self._timers = {"total": time.perf_counter()}
        
        # Record mode info in ablation config
        if self._current_run:
            self._current_run.ablation_config.update({
                "mode": mode,
                "sentiment_skipped": sentiment_skipped,
                "credibility_skipped": credibility_skipped,
            })
        
        logger.debug(f"[metrics] Started run {run_id} (mode={mode})")
    
    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self._timers[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> float:
        """Stop a named timer and return elapsed milliseconds."""
        if name not in self._timers:
            return 0.0
        elapsed_ms = (time.perf_counter() - self._timers[name]) * 1000
        
        # Map timer name to metric field
        if self._current_run:
            field_map = {
                "query_orchestrator": "query_orchestrator_ms",
                "external_retrieval": "external_retrieval_ms",
                "internal_retrieval": "internal_retrieval_ms",
                "sentiment": "sentiment_analysis_ms",
                "credibility": "credibility_analysis_ms",
                "theme_routing": "theme_routing_ms",
                "memory_consolidation": "memory_consolidation_ms",
                "theme_agents": "theme_agents_ms",
                "coordinator": "coordinator_ms",
            }
            if name in field_map:
                setattr(self._current_run, field_map[name], elapsed_ms)
        
        return elapsed_ms
    
    def record_query_metrics(self, queries_count: int, strategy: str) -> None:
        """Record query orchestrator metrics."""
        if self._current_run:
            self._current_run.queries_generated = queries_count
            self._current_run.query_strategy = strategy
    
    def record_retrieval_metrics(
        self,
        external_count: int,
        internal_count: int,
        after_dedup: int
    ) -> None:
        """Record document retrieval metrics."""
        if self._current_run:
            self._current_run.external_docs_count = external_count
            self._current_run.internal_docs_count = internal_count
            self._current_run.total_docs_count = external_count + internal_count
            self._current_run.docs_after_dedup = after_dedup
    
    def record_sentiment_metrics(
        self,
        positive: int,
        negative: int,
        neutral: int,
        agreement_rate: float
    ) -> None:
        """Record sentiment analysis metrics."""
        if self._current_run:
            self._current_run.sentiment_positive = positive
            self._current_run.sentiment_negative = negative
            self._current_run.sentiment_neutral = neutral
            self._current_run.sentiment_agreement_rate = agreement_rate
    
    def record_credibility_metrics(
        self,
        avg_score: float,
        high_count: int,
        low_count: int
    ) -> None:
        """Record credibility analysis metrics."""
        if self._current_run:
            self._current_run.avg_credibility_score = avg_score
            self._current_run.high_credibility_count = high_count
            self._current_run.low_credibility_count = low_count
    
    def record_theme_metrics(self, distribution: dict[str, int]) -> None:
        """Record theme routing metrics."""
        if self._current_run:
            self._current_run.theme_distribution = distribution
            self._current_run.themes_with_docs = sum(1 for v in distribution.values() if v > 0)
    
    def record_rag_metrics(
        self,
        chunks_retrieved: int,
        avg_relevance: float,
        chunks_stored: int
    ) -> None:
        """Record RAG metrics."""
        if self._current_run:
            self._current_run.rag_chunks_retrieved = chunks_retrieved
            self._current_run.rag_avg_relevance = avg_relevance
            self._current_run.memory_chunks_stored = chunks_stored
    
    def record_output_metrics(
        self,
        insights_count: int,
        insights_with_evidence: int,
        alerts_count: int
    ) -> None:
        """Record output quality metrics."""
        if self._current_run:
            self._current_run.insights_generated = insights_count
            self._current_run.insights_with_evidence = insights_with_evidence
            self._current_run.alerts_triggered = alerts_count
    
    def record_error(self, error: str) -> None:
        """Record an error that occurred during the run."""
        if self._current_run:
            self._current_run.errors.append(error)
    
    def record_fallback(self, fallback: str) -> None:
        """Record a fallback that was used."""
        if self._current_run:
            self._current_run.fallbacks_used.append(fallback)
    
    def end_run(self) -> PipelineMetrics | None:
        """End the current run and return metrics."""
        if not self._current_run:
            return None
        
        # Calculate total latency
        if "total" in self._timers:
            self._current_run.total_latency_ms = (
                time.perf_counter() - self._timers["total"]
            ) * 1000
        
        # Store completed run
        metrics = self._current_run
        self._completed_runs.append(metrics)
        
        # Trim history if needed
        if len(self._completed_runs) > self._max_history:
            self._completed_runs = self._completed_runs[-self._max_history:]
        
        # Save to file
        self._save_run(metrics)
        
        logger.info(
            f"[metrics] Run {metrics.run_id} completed: "
            f"{metrics.total_latency_ms:.0f}ms, "
            f"{metrics.docs_after_dedup} docs (raw: {metrics.total_docs_count}), "
            f"{metrics.insights_generated} insights"
        )
        
        self._current_run = None
        self._timers = {}
        
        return metrics
    
    def _save_run(self, metrics: PipelineMetrics) -> None:
        """Save metrics to JSON file."""
        try:
            # Daily file
            date_str = datetime.now().strftime("%Y-%m-%d")
            filepath = self._metrics_dir / f"metrics_{date_str}.jsonl"
            
            with open(filepath, "a") as f:
                f.write(json.dumps(metrics.to_dict()) + "\n")
                
        except Exception as e:
            logger.warning(f"[metrics] Failed to save metrics: {e}")
    
    def get_summary(self, last_n: int = 10) -> dict[str, Any]:
        """Get summary statistics from recent runs."""
        runs = self._completed_runs[-last_n:] if self._completed_runs else []
        
        if not runs:
            return {"message": "No metrics collected yet"}
        
        # Calculate averages
        avg_latency = sum(r.total_latency_ms for r in runs) / len(runs)
        avg_docs = sum(r.total_docs_count for r in runs) / len(runs)
        avg_insights = sum(r.insights_generated for r in runs) / len(runs)
        avg_agreement = sum(r.sentiment_agreement_rate for r in runs) / len(runs)
        avg_credibility = sum(r.avg_credibility_score for r in runs) / len(runs)
        
        # Error rate
        runs_with_errors = sum(1 for r in runs if r.errors)
        error_rate = runs_with_errors / len(runs)
        
        # Fallback rate
        runs_with_fallbacks = sum(1 for r in runs if r.fallbacks_used)
        fallback_rate = runs_with_fallbacks / len(runs)
        
        return {
            "runs_analyzed": len(runs),
            "avg_total_latency_ms": round(avg_latency, 1),
            "avg_documents": round(avg_docs, 1),
            "avg_insights": round(avg_insights, 1),
            "avg_sentiment_agreement": round(avg_agreement, 3),
            "avg_credibility_score": round(avg_credibility, 3),
            "error_rate": round(error_rate, 3),
            "fallback_rate": round(fallback_rate, 3),
            "latency_breakdown": {
                "query_orchestrator": round(sum(r.query_orchestrator_ms for r in runs) / len(runs), 1),
                "external_retrieval": round(sum(r.external_retrieval_ms for r in runs) / len(runs), 1),
                "internal_retrieval": round(sum(r.internal_retrieval_ms for r in runs) / len(runs), 1),
                "sentiment_analysis": round(sum(r.sentiment_analysis_ms for r in runs) / len(runs), 1),
                "credibility_analysis": round(sum(r.credibility_analysis_ms for r in runs) / len(runs), 1),
                "theme_agents": round(sum(r.theme_agents_ms for r in runs) / len(runs), 1),
            }
        }


# Global singleton
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
