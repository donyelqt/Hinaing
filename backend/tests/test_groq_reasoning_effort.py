"""A JSON stage on a reasoning model must ask for low reasoning effort.

The 23:43 narrative call returned 200 with an unterminated JSON string.
Strategy 5 recovered 203 characters, so the summary held one paragraph instead
of six.

gpt-oss-120b emits reasoning tokens before the JSON, and those tokens count
against max_tokens. The budget is 4000. Reasoning consumed about 3950 of it.

The OpenRouter provider already pins reasoning effort for this reason. The Groq
provider does not, so the same stage is reliable on one provider and not the
other.
"""
from __future__ import annotations

from app.services.llm.groq_provider import GroqProvider


def test_generate_sends_low_reasoning_effort() -> None:
    provider = GroqProvider.__new__(GroqProvider)
    provider._model = "openai/gpt-oss-120b"

    payload = provider._build_payload(
        prompt="Return JSON.",
        system_prompt=None,
        temperature=0.2,
        max_tokens=4000,
        stream=False,
    )

    assert payload["reasoning_effort"] == "low"


def test_a_caller_can_override_reasoning_effort() -> None:
    provider = GroqProvider.__new__(GroqProvider)
    provider._model = "openai/gpt-oss-120b"

    payload = provider._build_payload(
        prompt="Return JSON.",
        system_prompt=None,
        temperature=0.2,
        max_tokens=4000,
        stream=False,
        reasoning_effort="high",
    )

    assert payload["reasoning_effort"] == "high"