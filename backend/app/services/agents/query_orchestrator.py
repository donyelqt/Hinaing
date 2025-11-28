"""Adaptive query planning for the insights workflow."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

from ...schemas.snapshot import SnapshotRequest
from ...schemas.query import QueryPlan, QueryTask

logger = logging.getLogger(__name__)


@dataclass
class QueryOrchestratorAgent:
    """Heuristic query planner inspired by the Phase 2 design."""

    max_queries: int = 6
    fallback_focus: str = "public services"
    _risk_keywords: tuple[str, ...] = field(
        default=("risk", "alert", "outage", "emergency", "crisis"), init=False
    )

    def run(self, request: SnapshotRequest) -> QueryPlan:
        """Generate a query plan for downstream retrieval."""
        focus_values = request.focus_areas or [self.fallback_focus]
        time_window = request.time_window or "24h"

        logger.info(
            "[query_orchestrator] Planning queries",
            extra={"focus": focus_values, "window": time_window},
        )

        tasks: list[QueryTask] = []
        tasks.append(self._build_broad_task(focus_values, time_window))
        tasks.extend(self._build_targeted_tasks(focus_values, time_window))
        tasks.extend(self._build_risk_tasks(focus_values, time_window))

        deduped_tasks = self._deduplicate(tasks)
        prioritized = sorted(deduped_tasks, key=lambda t: t.priority)
        trimmed = prioritized[: self.max_queries]

        strategy_lines = [
            f"Time window: {time_window}.",
            f"Focus areas: {', '.join(focus_values)}.",
            f"Queries planned: {len(trimmed)} (broad + targeted + risk checks).",
        ]
        strategy = " ".join(strategy_lines)

        expected_results = [
            f"Validate latest developments for {focus.lower()} in Baguio City"
            for focus in focus_values
        ][:3]

        plan = QueryPlan(strategy=strategy, queries=trimmed, expected_results=expected_results)
        logger.info(
            "[query_orchestrator] Plan ready",
            extra={"query_count": len(plan.queries)},
        )
        return plan

    # Helper builders -----------------------------------------------------

    def _build_broad_task(self, focus: Iterable[str], window: str) -> QueryTask:
        focus_text = ", ".join(focus)
        query = f"Baguio City {focus_text} civic updates {window}"
        return QueryTask(query=query, intent="broad", priority=1)

    def _build_targeted_tasks(self, focus: Iterable[str], window: str) -> list[QueryTask]:
        tasks: list[QueryTask] = []
        for idx, area in enumerate(focus, start=2):
            query = f"{area} situation in Baguio City latest {window}"
            tasks.append(QueryTask(query=query, intent="targeted", priority=idx))
        return tasks

    def _build_risk_tasks(self, focus: Iterable[str], window: str) -> list[QueryTask]:
        tasks: list[QueryTask] = []
        for area in focus:
            if any(keyword in area.lower() for keyword in self._risk_keywords):
                query = f"{area} emergency reports Baguio City {window}"
            else:
                query = f"Baguio City {area} incident reports {window}"
            tasks.append(QueryTask(query=query, intent="risk", priority=5))
        if not tasks:
            tasks.append(
                QueryTask(
                    query=f"Baguio City civic risk alerts {window}",
                    intent="risk",
                    priority=5,
                )
            )
        return tasks

    def _deduplicate(self, tasks: Iterable[QueryTask]) -> list[QueryTask]:
        seen: set[str] = set()
        unique: list[QueryTask] = []
        for task in tasks:
            key = task.query.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            unique.append(task)
        return unique
