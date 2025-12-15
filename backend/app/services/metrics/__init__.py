"""Metrics collection module for thesis evaluation."""
from .collector import (
    MetricsCollector,
    PipelineMetrics,
    get_metrics_collector,
)

__all__ = [
    "MetricsCollector",
    "PipelineMetrics",
    "get_metrics_collector",
]
