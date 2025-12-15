"""Metrics API endpoints for thesis evaluation."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from ..services.metrics import get_metrics_collector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
async def get_metrics_summary(last_n: int = Query(default=10, ge=1, le=100)):
    """Get summary statistics from recent pipeline runs.
    
    Returns aggregated metrics useful for thesis evaluation:
    - Average latency per component
    - Document counts
    - Sentiment agreement rates
    - Error/fallback rates
    """
    collector = get_metrics_collector()
    return collector.get_summary(last_n=last_n)


@router.get("/recent")
async def get_recent_runs(limit: int = Query(default=10, ge=1, le=50)):
    """Get detailed metrics from recent pipeline runs."""
    collector = get_metrics_collector()
    runs = collector._completed_runs[-limit:]
    return {
        "count": len(runs),
        "runs": [r.to_dict() for r in runs]
    }


@router.get("/export")
async def export_metrics(date: str | None = None):
    """Export metrics for a specific date (YYYY-MM-DD format).
    
    Returns all metrics collected on that date for thesis analysis.
    """
    metrics_dir = Path("backend/data/metrics")
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    filepath = metrics_dir / f"metrics_{date}.jsonl"
    
    if not filepath.exists():
        return {"message": f"No metrics found for {date}", "runs": []}
    
    runs = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                runs.append(json.loads(line))
    
    return {
        "date": date,
        "count": len(runs),
        "runs": runs
    }


@router.get("/comparison")
async def get_comparison_metrics():
    """Get metrics formatted for thesis comparison tables.
    
    Returns data structured for:
    - Baseline vs Enhanced comparison
    - Component-wise latency breakdown
    - Quality metrics (sentiment agreement, credibility)
    """
    collector = get_metrics_collector()
    summary = collector.get_summary(last_n=50)
    
    if "message" in summary:
        return summary
    
    return {
        "performance": {
            "total_latency_ms": summary["avg_total_latency_ms"],
            "latency_breakdown": summary["latency_breakdown"],
        },
        "quality": {
            "sentiment_agreement_rate": summary["avg_sentiment_agreement"],
            "avg_credibility_score": summary["avg_credibility_score"],
            "avg_insights_per_run": summary["avg_insights"],
        },
        "reliability": {
            "error_rate": summary["error_rate"],
            "fallback_rate": summary["fallback_rate"],
        },
        "throughput": {
            "avg_documents_processed": summary["avg_documents"],
        },
        "sample_size": summary["runs_analyzed"],
    }
