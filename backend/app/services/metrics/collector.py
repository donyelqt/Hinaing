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

    # Faithfulness metrics (Node 7)
    faithfulness_total_claims: int = 0
    faithfulness_verified_claims: int = 0
    faithfulness_score: float = 0.0
    faithfulness_rate: float = 0.0  # verified_claims / total_claims

    # Citation Accuracy metrics (NEW - verifies citation truthfulness)
    citation_total: int = 0  # Total citations found in summary
    citation_valid: int = 0  # Citations with accurate metadata and matching source
    citation_accuracy_rate: float = 0.0  # valid / total (target: ≥0.90)

    # Hallucination Detection metrics (NEW - best practice separation)
    hallucination_count: int = 0  # TRUE hallucinations (fabricated claims)
    hallucination_rate: float = 0.0  # hallucinations / total_claims (target: 0.0)
    hallucination_types: dict[str, int] = field(default_factory=dict)
    is_hallucination_free: bool = True
    
    # Misattribution metrics (NEW - separate from hallucination)
    misattribution_count: int = 0  # Claims true but cited to wrong source
    misattribution_rate: float = 0.0  # misattributions / total_claims
    
    # Numerical hallucination metrics (NEW)
    numerical_hallucination_count: int = 0  # Fabricated numbers
    numerical_hallucination_rate: float = 0.0

    # Agentic Verification Rate (5-signal credibility)
    agentic_verification_total: int = 0  # Total documents verified
    agentic_verification_verified: int = 0  # Documents with verification_status="verified"
    agentic_verification_rate: float = 0.0  # verified / total (target: ≥0.97)

    # VSEE Effectiveness Metrics (Vector-Symbolic Epistemic Entailment)
    vsee_triggered_count: int = 0  # Documents where VSEE bypass was activated
    vsee_bypass_rate: float = 0.0  # vsee_triggered / total_docs
    vsee_api_calls_avoided: int = 0  # External API calls skipped via VSEE (Tavily + Fact Check)
    vsee_verified_via_crossref: int = 0  # Verified via crossref ≥ 0.70 + domain ≥ 0.45
    vsee_verified_via_domain: int = 0  # Verified via domain ≥ 0.70 + crossref ≥ 0.55
    
    # VSEE Quality Metrics (NEW - proves VSEE accuracy)
    vsee_avg_credibility_score: float = 0.0  # Avg credibility of VSEE-triggered docs
    vsee_high_credibility_rate: float = 0.0  # % of VSEE docs with score ≥ 0.75
    vsee_api_agreement_rate: float = 0.0  # When API worked, did VSEE agree?

    # API Cost Reduction / Cache Intelligence Rate
    api_calls_total: int = 0  # Total API calls if no caching
    api_calls_actual: int = 0  # Actual API calls made (after Smart Reuse)
    api_calls_saved: int = 0  # API calls saved via Smart Reuse
    api_cost_reduction_rate: float = 0.0  # saved / total (target: ≥0.81)
    smart_reuse_rate: float = 0.0  # already_enriched / total_docs (cache hit rate)
    documents_cached: int = 0  # Documents reused from cache
    documents_fresh: int = 0  # New documents requiring analysis

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
        
        # File path for persistent storage - use absolute path from project root
        import os
        # Find project root (parent of backend/app)
        current_file = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        self._metrics_dir = Path(project_root) / "backend" / "data" / "metrics"
        self._metrics_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[metrics] MetricsCollector initialized, saving to: {self._metrics_dir}")
    
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

    def record_faithfulness_metrics(
        self,
        total_claims: int,
        verified_claims: int,
        faithfulness_score: float,
        citation_verification: dict[str, Any] | None = None,
        hallucination_analysis: dict[str, Any] | None = None,
    ) -> None:
        """Record faithfulness verification metrics (Node 7).

        Args:
            total_claims: Total number of claims extracted from summary
            verified_claims: Number of claims entailed by source documents
            faithfulness_score: verified_claims / total_claims (0.0-1.0)
            citation_verification: Citation accuracy report from FaithfulnessAgent
            hallucination_analysis: Hallucination detection report from FaithfulnessAgent
        """
        if self._current_run:
            self._current_run.faithfulness_total_claims = total_claims
            self._current_run.faithfulness_verified_claims = verified_claims
            self._current_run.faithfulness_score = round(faithfulness_score, 3)
            self._current_run.faithfulness_rate = round(
                verified_claims / total_claims if total_claims > 0 else 0.0,
                3
            )

            # Record citation accuracy metrics (NEW)
            if citation_verification:
                self._current_run.citation_total = citation_verification.get("total_citations", 0)
                self._current_run.citation_valid = citation_verification.get("valid_citations", 0)
                self._current_run.citation_accuracy_rate = round(
                    citation_verification.get("citation_accuracy_rate", 0.0),
                    3
                )
                logger.info(
                    f"[metrics] Citation Accuracy: {self._current_run.citation_valid}/"
                    f"{self._current_run.citation_total} "
                    f"({self._current_run.citation_accuracy_rate:.3f})"
                )

            # Record hallucination detection metrics (NEW - best practice separation)
            if hallucination_analysis:
                # TRUE hallucinations
                h_analysis = hallucination_analysis.get("hallucination_analysis", {})
                self._current_run.hallucination_count = h_analysis.get("hallucination_count", 0)
                self._current_run.hallucination_rate = h_analysis.get("hallucination_rate", 0.0)
                self._current_run.hallucination_types = h_analysis.get("hallucination_types", {})
                self._current_run.is_hallucination_free = h_analysis.get("is_hallucination_free", True)
                
                # Misattribution (separate from hallucination)
                m_analysis = hallucination_analysis.get("misattribution_analysis", {})
                self._current_run.misattribution_count = m_analysis.get("misattribution_count", 0)
                self._current_run.misattribution_rate = m_analysis.get("misattribution_rate", 0.0)
                
                # Numerical hallucinations
                n_analysis = hallucination_analysis.get("numerical_hallucinations", {})
                self._current_run.numerical_hallucination_count = n_analysis.get("count", 0)
                self._current_run.numerical_hallucination_rate = n_analysis.get("rate", 0.0)
                
                logger.info(
                    f"[metrics] Hallucination Detection: {self._current_run.hallucination_count} hallucinations, "
                    f"{self._current_run.misattribution_count} misattributions, "
                    f"{self._current_run.numerical_hallucination_count} numerical hallucinations, "
                    f"hallucination_free={self._current_run.is_hallucination_free}"
                )
            else:
                logger.info(
                    f"[metrics] Faithfulness: {verified_claims}/{total_claims} "
                    f"({faithfulness_score:.3f})"
                )

    def record_agentic_verification_rate(
        self,
        total_documents: int,
        verified_documents: int,
    ) -> None:
        """Record Agentic Verification Rate (5-signal credibility).

        Args:
            total_documents: Total documents processed by CredibilityAgent
            verified_documents: Documents with verification_status="verified"
        """
        if self._current_run:
            self._current_run.agentic_verification_total = total_documents
            self._current_run.agentic_verification_verified = verified_documents
            self._current_run.agentic_verification_rate = round(
                verified_documents / total_documents if total_documents > 0 else 0.0,
                3
            )
            logger.info(
                f"[metrics] Agentic Verification Rate: {verified_documents}/{total_documents} "
                f"({self._current_run.agentic_verification_rate:.3f})"
            )

    def record_vsee_effectiveness(
        self,
        triggered_count: int,
        bypass_rate: float,
        api_calls_avoided: int,
        verified_via_crossref: int = 0,
        verified_via_domain: int = 0,
        avg_credibility_score: float = 0.0,
        high_credibility_rate: float = 0.0,
        api_agreement_rate: float = 0.0,
    ) -> None:
        """Record VSEE (Vector-Symbolic Epistemic Entailment) effectiveness metrics.

        Args:
            triggered_count: Number of documents where VSEE bypass was activated
            bypass_rate: triggered_count / total_documents
            api_calls_avoided: External API calls skipped via VSEE (Tavily + Fact Check)
            verified_via_crossref: Documents verified via crossref ≥ 0.70 + domain ≥ 0.45
            verified_via_domain: Documents verified via domain ≥ 0.70 + crossref ≥ 0.55
            avg_credibility_score: Average credibility score of VSEE-triggered documents
            high_credibility_rate: % of VSEE-triggered docs with credibility ≥ 0.75
            api_agreement_rate: When APIs worked, how often did VSEE agree?
        """
        if self._current_run:
            self._current_run.vsee_triggered_count = triggered_count
            self._current_run.vsee_bypass_rate = round(bypass_rate, 3)
            self._current_run.vsee_api_calls_avoided = api_calls_avoided
            self._current_run.vsee_verified_via_crossref = verified_via_crossref
            self._current_run.vsee_verified_via_domain = verified_via_domain
            self._current_run.vsee_avg_credibility_score = round(avg_credibility_score, 3)
            self._current_run.vsee_high_credibility_rate = round(high_credibility_rate, 3)
            self._current_run.vsee_api_agreement_rate = round(api_agreement_rate, 3)

            logger.info(
                f"[metrics] VSEE Effectiveness: triggered={triggered_count} "
                f"({bypass_rate:.1%}), API calls avoided={api_calls_avoided}, "
                f"avg_credibility={avg_credibility_score:.3f}, "
                f"high_cred_rate={high_credibility_rate:.1%}"
            )

    def record_api_cost_reduction(
        self,
        api_calls_total: int,
        api_calls_actual: int,
        documents_cached: int,
        documents_fresh: int,
    ) -> None:
        """Record API Cost Reduction / Cache Intelligence Rate (Smart Reuse).

        Args:
            api_calls_total: Total API calls if no caching (len(documents) * 2 for sentiment + credibility)
            api_calls_actual: Actual API calls made after Smart Reuse
            documents_cached: Documents reused from cache (already enriched)
            documents_fresh: New documents requiring full analysis
        """
        if self._current_run:
            self._current_run.api_calls_total = api_calls_total
            self._current_run.api_calls_actual = api_calls_actual
            self._current_run.api_calls_saved = api_calls_total - api_calls_actual
            self._current_run.api_cost_reduction_rate = round(
                (api_calls_total - api_calls_actual) / api_calls_total if api_calls_total > 0 else 0.0,
                3
            )
            self._current_run.smart_reuse_rate = round(
                documents_cached / (documents_cached + documents_fresh) if (documents_cached + documents_fresh) > 0 else 0.0,
                3
            )
            self._current_run.documents_cached = documents_cached
            self._current_run.documents_fresh = documents_fresh
            
            logger.info(
                f"[metrics] API Cost Reduction: {self._current_run.api_cost_reduction_rate:.1%} "
                f"({self._current_run.api_calls_saved}/{api_calls_total} calls saved, "
                f"{documents_cached} cached / {documents_fresh} fresh)"
            )

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
        
        # NEW: Agentic Verification Rate and API Cost Reduction
        avg_verification_rate = sum(r.agentic_verification_rate for r in runs) / len(runs) if runs else 0
        avg_cost_reduction = sum(r.api_cost_reduction_rate for r in runs) / len(runs) if runs else 0
        avg_smart_reuse = sum(r.smart_reuse_rate for r in runs) / len(runs) if runs else 0
        
        # NEW: VSEE Effectiveness
        avg_vsee_bypass_rate = sum(r.vsee_bypass_rate for r in runs) / len(runs) if runs else 0
        avg_vsee_api_avoided = sum(r.vsee_api_calls_avoided for r in runs) / len(runs) if runs else 0
        avg_vsee_credibility = sum(r.vsee_avg_credibility_score for r in runs) / len(runs) if runs else 0
        avg_vsee_high_cred_rate = sum(r.vsee_high_credibility_rate for r in runs) / len(runs) if runs else 0

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
            "avg_agentic_verification_rate": round(avg_verification_rate, 3),
            "avg_api_cost_reduction_rate": round(avg_cost_reduction, 3),
            "avg_smart_reuse_rate": round(avg_smart_reuse, 3),
            "vsee": {
                "avg_bypass_rate": round(avg_vsee_bypass_rate, 3),
                "avg_api_calls_avoided": round(avg_vsee_api_avoided, 1),
                "avg_credibility_score": round(avg_vsee_credibility, 3),
                "avg_high_credibility_rate": round(avg_vsee_high_cred_rate, 3),
            },
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
