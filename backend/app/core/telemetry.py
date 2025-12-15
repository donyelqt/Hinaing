"""Telemetry service for scientific research metrics and structured logging.

This module provides tools to record precise measurements (latency, token usage, tool invocation)
separate from standard application logs. It produces a JSONL file suitable for 
statistical analysis dataframes (pandas/R).
"""
import time
import json
import logging
import functools
import uuid
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
from pathlib import Path

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
METRICS_FILE = LOG_DIR / "research_metrics.jsonl"

class TelemetryService:
    def __init__(self):
        self.run_id = str(uuid.uuid4())
        self._setup_logger()

    def _setup_logger(self):
        """Configure a specific logger that only writes JSONL to the metrics file."""
        self.logger = logging.getLogger("research_telemetry")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't bubble up to root logger

        # Avoid adding multiple handlers if re-initialized
        if not self.logger.handlers:
            handler = logging.FileHandler(METRICS_FILE)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(
        self, 
        event_type: str, 
        component: str, 
        metrics: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a structured research event.

        Args:
            event_type: Category of event (e.g., "agency_execution", "latency_test", "token_usage")
            component: Name of the system component (e.g., "QueryOrchestrator")
            metrics: Quantitative data (e.g., {"latency_ms": 120, "items_processed": 5})
            metadata: Qualitative context (e.g., {"query": "baguio traffic", "model": "gemini-2.5"})
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "event_type": event_type,
            "component": component,
            "metrics": metrics,
            "metadata": metadata or {}
        }
        self.logger.info(json.dumps(entry))

    def start_run(self) -> str:
        """Generate a new run ID for a session."""
        self.run_id = str(uuid.uuid4())
        return self.run_id

# Global instance
telemetry = TelemetryService()

def measure_performance(component: str, operation: str):
    """Decorator to measure latency and success/failure of a function."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_type = type(e).__name__
                raise
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                telemetry.log_event(
                    event_type="performance_trace",
                    component=component,
                    metrics={
                        "latency_ms": round(duration_ms, 2),
                        "success": int(success)
                    },
                    metadata={
                        "operation": operation,
                        "error_type": error_type
                    }
                )
        return wrapper
    return decorator
