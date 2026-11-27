"""The gate must count prompt tokens, not only output tokens.

The provider counts prompt plus max_tokens against the per-minute allowance. The
gate reserved max_tokens alone, so a call whose prompt was 2287 tokens larger
than the reservation was admitted and then rejected.

A prompt estimate closes that gap. It is deliberately generous, because
under-counting is what causes the 429 and over-counting only waits.
"""
from __future__ import annotations

from app.core.token_rate_gate import TokenRateGate


def test_prompt_allowance_is_added_to_the_reservation() -> None:
    gate = TokenRateGate(tpm=8000)
    gate.acquire(2500, prompt_tokens=2287)

    assert gate.used() == 4787


def test_a_call_that_fits_with_prompt_is_admitted() -> None:
    gate = TokenRateGate(tpm=8000)

    waited = gate.acquire(2500, prompt_tokens=1000)

    assert waited == 0.0
    assert gate.used() == 3500


def test_a_call_that_breaches_with_prompt_waits() -> None:
    gate = TokenRateGate(tpm=8000, window=0.3)
    gate.acquire(4000, prompt_tokens=1000)

    gate.acquire(2500, prompt_tokens=1000)

    assert gate.used() == 3500


def test_default_prompt_allowance_is_conservative() -> None:
    gate = TokenRateGate(tpm=8000)
    gate.acquire(2500)

    assert gate.used() > 2500