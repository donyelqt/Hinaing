"""One shared token-rate gate for every LLM call in the process.

The provider counts prompt plus max_tokens against a per-minute allowance shared
per organisation. Calls from different stages overlap, so two calls that each fit
alone can breach together. A lock cannot fix that, because the allowance is a
rolling window and not a concurrency count.

The gate records what each call reserved, waits when the trailing 60 seconds
would exceed the ceiling, and records the actual usage the provider reports so
the next decision is exact rather than estimated.
"""
from __future__ import annotations

import threading
import time

DEFAULT_TPM = 8000
WINDOW_SECONDS = 60.0

# The provider counts prompt tokens too, and the gate cannot see them before the
# call. This is a deliberately generous per-call allowance, so the reservation
# over-counts rather than under-counts.
DEFAULT_PROMPT_ALLOWANCE = 1200


class TokenRateGate:
    """Reserves output tokens against a rolling per-minute ceiling."""

    def __init__(self, tpm: int = DEFAULT_TPM, window: float = WINDOW_SECONDS) -> None:
        self._tpm = tpm
        self._window = window
        self._lock = threading.Lock()
        self._spent: list[tuple[float, int]] = []

    def _prune(self, now: float) -> None:
        cutoff = now - self._window
        self._spent = [(at, n) for at, n in self._spent if at > cutoff]

    def used(self, now: float | None = None) -> int:
        with self._lock:
            self._prune(now if now is not None else time.monotonic())
            return sum(n for _, n in self._spent)

    def acquire(
        self,
        reserved: int,
        *,
        prompt_tokens: int | None = None,
        wait_seconds: float = 30.0,
    ) -> float:
        """Block until the call fits, then record it. Returns seconds waited.

        \`prompt_tokens\` is what the caller knows about the prompt. When it is
        not given, the allowance is used, so the reservation errs high.
        """
        total = reserved + (DEFAULT_PROMPT_ALLOWANCE if prompt_tokens is None else prompt_tokens)
        deadline = time.monotonic() + wait_seconds
        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                self._prune(now)
                if sum(n for _, n in self._spent) + total <= self._tpm:
                    self._spent.append((now, total))
                    return waited
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                # The caller proceeds and the provider's own retry handles it.
                return waited
            time.sleep(min(0.25, remaining))
            waited += 0.25

    def record(self, actual: int) -> None:
        """Replace the last reservation with what the provider reported."""
        with self._lock:
            if not self._spent:
                self._spent.append((time.monotonic(), actual))
                return
            at, reserved = self._spent[-1]
            self._spent[-1] = (at, actual if actual > 0 else reserved)


GATE = TokenRateGate()