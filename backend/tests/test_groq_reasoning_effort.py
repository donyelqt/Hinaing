"""Reasoning effort must reach the wire on any pinned SDK build.

#410 passed reasoning_effort as a top-level keyword. The Space resolved a groq
build whose create() has no such parameter, so every call raised
"unexpected keyword argument 'reasoning_effort'" and the theme agents failed.

extra_body is forwarded to the request body by every groq SDK build, so the
parameter reaches the API regardless of the installed signature.
"""
from __future__ import annotations

from app.services.llm.groq_provider import GroqProvider


def _payload(**kwargs) -> dict:
    provider = GroqProvider.__new__(GroqProvider)
    provider._model = "openai/gpt-oss-120b"
    return provider._build_payload(
        prompt="Return JSON.",
        system_prompt=None,
        temperature=0.2,
        max_tokens=4000,
        stream=False,
        **kwargs,
    )


def test_reasoning_effort_rides_in_extra_body() -> None:
    payload = _payload()

    assert payload["extra_body"] == {"reasoning_effort": "low"}
    assert "reasoning_effort" not in payload


def test_a_caller_override_replaces_it() -> None:
    payload = _payload(reasoning_effort="high")

    assert payload["extra_body"] == {"reasoning_effort": "high"}


def test_stream_still_sets_stream() -> None:
    provider = GroqProvider.__new__(GroqProvider)
    provider._model = "openai/gpt-oss-120b"

    payload = provider._build_payload(
        prompt="p",
        system_prompt=None,
        temperature=0.2,
        max_tokens=100,
        stream=True,
    )

    assert payload["stream"] is True