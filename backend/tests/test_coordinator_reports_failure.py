"""Regression test: the coordinator must not report success on a failed narrative.

Guards the prod run where a swallowed 429 logged "Narrative generation
complete" and the card rendered a blank overall sentiment.
"""
import asyncio

from app.services.agents.coordinator_agent import CoordinatorAgent


class _Client:
    is_available = True

    def __init__(self, summary, error=None):
        self._summary = summary
        self._error = error

    async def analyze_snapshot(self, **kwargs):
        if self._error is not None:
            raise self._error
        return self._summary, []


def _agent(client) -> CoordinatorAgent:
    agent = CoordinatorAgent.__new__(CoordinatorAgent)
    agent._client = client  # type: ignore[assignment]
    return agent


def test_failure_returns_no_summary():
    agent = _agent(_Client(None, error=RuntimeError("429 rate limit")))

    summary, insights = asyncio.run(
        agent.run(window="6h", focus_areas=["health"], documents=[])
    )

    assert summary is None
    assert insights == []


def test_empty_summary_is_not_reported_as_success(caplog):
    agent = _agent(_Client(None))

    with caplog.at_level("INFO", logger="app.services.agents.coordinator_agent"):
        summary, _ = asyncio.run(
            agent.run(window="6h", focus_areas=["health"], documents=[])
        )

    assert summary is None
    assert "Narrative generation complete" not in caplog.text


def test_success_returns_summary():
    agent = _agent(_Client("A narrative with citations."))

    summary, _ = asyncio.run(
        agent.run(window="6h", focus_areas=["health"], documents=[])
    )

    assert summary == "A narrative with citations."