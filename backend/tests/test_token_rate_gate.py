"""The gate must admit a call that fits and wait for one that does not.

The provider counts prompt plus max_tokens against a per-minute allowance. Two
calls that each fit alone can breach together, so the gate tracks the trailing
window and records what the provider actually used.
"""
from __future__ import annotations

import time

from app.core.token_rate_gate import TokenRateGate


def test_a_call_that_fits_is_recorded_at_once() -> None:
    gate = TokenRateGate(tpm=8000)

    waited = gate.acquire(4000, prompt_tokens=0)

    assert waited == 0.0
    assert gate.used() == 4000


def test_a_call_that_would_breach_waits_for_the_window() -> None:
    gate = TokenRateGate(tpm=8000, window=0.3)
    gate.acquire(5000, prompt_tokens=0)

    start = time.monotonic()
    gate.acquire(5000, prompt_tokens=0)
    elapsed = time.monotonic() - start

    assert elapsed >= 0.25, elapsed


def test_usage_replaces_the_reservation() -> None:
    gate = TokenRateGate(tpm=8000)
    gate.acquire(4000, prompt_tokens=0)

    gate.record(1200)

    assert gate.used() == 1200


def test_a_zero_report_keeps_the_reservation() -> None:
    gate = TokenRateGate(tpm=8000)
    gate.acquire(4000, prompt_tokens=0)

    gate.record(0)

    assert gate.used() == 4000