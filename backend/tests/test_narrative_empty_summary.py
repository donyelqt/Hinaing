"""A JSON answer with no summary must still yield the text.

The 23:02 run logged "Narrative generated" and then "returned no summary" with
no parse-failure line. That means the JSON parsed and the summary field was
empty or absent, which the caller treats as a failed run.
"""
from __future__ import annotations

import asyncio

from app.services.nlp.narrative import LLMNarrativeClient


class _LLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    async def generate(self, **kwargs):
        return self._reply


def _client(reply: str) -> LLMNarrativeClient:
    client = LLMNarrativeClient.__new__(LLMNarrativeClient)
    client._resolve_model = lambda mode=None: _LLM(reply)  # type: ignore[assignment]
    return client


def test_insights_only_json_returns_the_raw_text() -> None:
    raw = '{"insights": [{"category": "Safety", "title": "Fire", "detail": "d"}]}'

    summary, _ = asyncio.run(_client(raw)._run_direct_generation(
        window="6h", focus_areas=["safety"], documents=[],
    ))

    assert summary is not None
    assert "insights" in summary


def test_empty_summary_returns_the_raw_text() -> None:
    raw = '{"summary": "", "insights": []}'

    summary, _ = asyncio.run(_client(raw)._run_direct_generation(
        window="6h", focus_areas=["safety"], documents=[],
    ))

    assert summary is not None
    assert summary != ""


def test_a_real_summary_is_returned() -> None:
    raw = '{"summary": "Baguio fire incidents fell 27%.", "insights": []}'

    summary, _ = asyncio.run(_client(raw)._run_direct_generation(
        window="6h", focus_areas=["safety"], documents=[],
    ))

    assert summary == "Baguio fire incidents fell 27%."