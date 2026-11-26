"""A generated search query is not allowed to leave Baguio City.

The fallback generator used to emit bare keyword pairs such as
``("earthquake drill" OR "accident report")`` with no geographic anchor, and
the AI planner's output was accepted with no anchor check. LangSearch answers
those with national and foreign news.
"""
from __future__ import annotations

from app.schemas.snapshot import SnapshotRequest
from app.services.agents.query_orchestrator import QueryOrchestratorAgent
from app.services.insights.agent_tools import BAGUIO_LOCATION_TERMS


def _plan(queries: list[str]):
    agent = QueryOrchestratorAgent()
    request = SnapshotRequest(query="safety concerns", platforms=["web"])
    return agent._fallback_plan(request.focus_areas or ["safety"], "24h")


def test_fallback_queries_all_name_baguio() -> None:
    plan = _plan([])

    assert plan.queries
    for task in plan.queries:
        haystack = f"{task.query} {task.topic}".lower()
        assert any(term in haystack for term in BAGUIO_LOCATION_TERMS), task.query


def test_ai_synthesized_query_without_a_baguio_anchor_is_rejected() -> None:
    agent = QueryOrchestratorAgent()
    output = (
        'Final Answer: {"strategy": "x", "queries": ['
        '{"query": "earthquake drill Philippines schools", "topic": "earthquake drill", '
        '"focus_area": "safety", "intent": "targeted"},'
        '{"query": "road accident Davao City highway", "topic": "road accident", '
        '"focus_area": "safety", "intent": "targeted"}]}'
    )

    plan = agent._parse_synthesis_output(output, ["safety"], " after:2026-11-25")

    assert plan is None or plan.queries == []


def test_ai_synthesized_query_with_a_baguio_anchor_is_kept() -> None:
    agent = QueryOrchestratorAgent()
    output = (
        'Final Answer: {"strategy": "x", "queries": ['
        '{"query": "Baguio City earthquake drill schools", "topic": "earthquake drill", '
        '"focus_area": "safety", "intent": "targeted"}]}'
    )

    plan = agent._parse_synthesis_output(output, ["safety"], " after:2026-11-25")

    assert plan is not None
    assert len(plan.queries) == 1
    assert "Baguio City" in plan.queries[0].query