"""Fallback queries within one focus area must be semantically distinct.

BGE-large embeds the deterministic keyword pairs at 0.76 to 0.84 because they
are all Baguio civic text. LangSearch answers several of them with the same
URLs, so the pool collapses and the run starves.

The AI planner measured 0.56 to 0.66 on the same model, so only the
deterministic path is gated.
"""
from __future__ import annotations

from app.services.agents.query_orchestrator import QueryOrchestratorAgent
from app.services.insights.agent_tools import BAGUIO_LOCATION_TERMS

AREAS = ["safety", "infrastructure", "health", "tourism", "economy", "environment"]


def test_same_area_queries_are_semantically_distinct() -> None:
    agent = QueryOrchestratorAgent()

    plan = agent._fallback_plan(["health"], "24h")

    topics = [q.topic for q in plan.queries]
    assert len(topics) == len(set(topics))


def test_every_kept_query_still_names_baguio() -> None:
    agent = QueryOrchestratorAgent()

    plan = agent._fallback_plan(AREAS, "24h")

    assert plan.queries
    for task in plan.queries:
        haystack = f"{task.query} {task.topic}".lower()
        assert any(term in haystack for term in BAGUIO_LOCATION_TERMS), task.query


def test_fallback_still_covers_every_focus_area() -> None:
    agent = QueryOrchestratorAgent()

    plan = agent._fallback_plan(AREAS, "24h")

    covered = {q.focus_area for q in plan.queries if q.focus_area}
    assert covered == set(AREAS)