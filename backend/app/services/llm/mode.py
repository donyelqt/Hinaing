"""Request-scoped LLM execution mode.

Hinaing ships two interchangeable backends behind one interface:

- ``cloud`` -> hosted inference — Groq (``groq/compound``) everywhere except
  Node 1 query orchestration, which uses Gemini 2.5 Flash Lite (fastest
  per-inference and cheapest for its multi-iteration ReAct loop).
- ``local`` -> Ollama serving Qwen (``qwen2.5:3b``), fully offline.

A request carries the choice in its ``llm_mode`` field. Because agents are
module-level singletons shared across concurrent requests, the active mode is
kept in a :class:`~contextvars.ContextVar` instead of being threaded through
every call signature. That keeps ``get_llm_for_mode()`` a drop-in replacement
for the old per-node settings lookup.

Mode never degrades silently: a request that asks for ``local`` and cannot reach
Ollama raises, rather than quietly spending cloud quota.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Literal

from ...core.config import get_settings

logger = logging.getLogger(__name__)

LLMMode = Literal["cloud", "local"]

CLOUD: LLMMode = "cloud"
LOCAL: LLMMode = "local"
VALID_LLM_MODES: tuple[LLMMode, ...] = (CLOUD, LOCAL)

# Provider identifier per mode. Kept as strings so they can be handed straight to
# the provider factory and logged without a second mapping table.
_MODE_PROVIDER: dict[LLMMode, str] = {CLOUD: "groq", LOCAL: "local"}

_active_mode: ContextVar[str] = ContextVar("hinaing_llm_mode", default=CLOUD)


class InvalidLLMMode(ValueError):
    """Raised when a request supplies an ``llm_mode`` outside the supported set."""


def default_llm_mode() -> str:
    """Mode used when a request omits ``llm_mode``."""
    return str(get_settings().llm_mode)


def normalize_llm_mode(value: str | None) -> str:
    """Coerce arbitrary input to a valid mode string.

    ``None``/empty falls back to the configured default. Anything else must be
    exactly ``cloud`` or ``local`` (case-insensitive, surrounding whitespace
    tolerated) — unknown values raise instead of defaulting, so a typo in the
    frontend surfaces as a 422 rather than a surprise bill.
    """
    if value is None:
        return default_llm_mode()
    candidate = str(value).strip().lower()
    if not candidate:
        return default_llm_mode()
    if candidate not in VALID_LLM_MODES:
        raise InvalidLLMMode(
            f"Unsupported llm_mode {value!r}; expected one of {', '.join(VALID_LLM_MODES)}"
        )
    return candidate


def get_active_llm_mode() -> str:
    """Mode in effect for the current request."""
    return _active_mode.get()


def provider_name_for_mode(mode: str | None = None) -> str:
    """Provider identifier (``gemini``/``groq``/``local``) backing ``mode``.

    Cloud mode resolves to the default cloud provider (``groq``); Node 1
    overrides to Gemini via :func:`app.services.llm.factory.get_cloud_llm`.
    """
    return _MODE_PROVIDER[normalize_llm_mode(mode)]  # type: ignore[index]


@contextmanager
def llm_mode_scope(mode: str | None) -> Iterator[str]:
    """Bind ``mode`` for the duration of the block, restoring the previous value.

    Context is copied into ``asyncio`` tasks and threads spawned via
    ``contextvars.copy_context()``, which covers the pipeline's ``to_thread`` and
    ``run_in_executor`` hops. ``asyncio.to_thread`` propagates context
    automatically; raw ``ThreadPoolExecutor.submit`` does not, so call sites that
    hand work to ``GLOBAL_EXECUTOR`` pass the mode explicitly instead.
    """
    resolved = normalize_llm_mode(mode)
    token: Token[str] = _active_mode.set(resolved)
    try:
        yield resolved
    finally:
        _active_mode.reset(token)


def describe_active_llm() -> str:
    """Human-readable ``mode`` + provider name, for logs and API responses."""
    mode = get_active_llm_mode()
    return f"{mode} ({_MODE_PROVIDER[mode]})"  # type: ignore[index]
