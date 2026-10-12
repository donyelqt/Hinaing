"""LLM provider factory: Gemini/Groq (cloud) and Ollama/Qwen (local).

Provider choice is driven by the request-scoped ``llm_mode`` (see
:mod:`app.services.llm.mode`). Cloud mode picks the backend per call site via
:func:`get_cloud_llm` — Node 1 query orchestration uses Gemini 2.5 Flash Lite
(fastest per-inference and cheapest for multi-iteration ReAct), everything else
uses Groq ``groq/compound``. Local mode is always Ollama and never touches a
cloud provider. Every backend implements :class:`BaseLLMProvider`, so call
sites only ever see ``generate`` / ``generate_json`` / ``generate_stream``.
"""
from __future__ import annotations

import logging

from ...core.config import get_settings
from .base import BaseLLMProvider
from .mode import get_active_llm_mode, normalize_llm_mode

logger = logging.getLogger(__name__)

# Provider identifiers accepted by :func:`get_llm_provider`.
PROVIDER_GEMINI = "gemini"
PROVIDER_GROQ = "groq"
PROVIDER_LOCAL = "local"
SUPPORTED_PROVIDERS: tuple[str, ...] = (PROVIDER_GEMINI, PROVIDER_GROQ, PROVIDER_LOCAL)


def get_llm_provider(
    provider: str,
    *,
    model: str | None = None,
) -> BaseLLMProvider:
    """Return the provider client for ``provider``.

    Instances are cached per model name (see ``get_groq_provider`` /
    ``get_ollama_provider``), so repeated calls are cheap and reuse the same
    pooled HTTP client.

    Args:
        provider: ``"gemini"``/``"groq"`` for cloud inference, ``"local"``
            for Ollama.
        model: Optional model override. Defaults to the model configured for
            that provider in settings.
    """
    settings = get_settings()

    if provider == PROVIDER_GEMINI:
        from .gemini_provider import get_gemini_provider

        client = get_gemini_provider(model or settings.gemini_default_model)
    elif provider == PROVIDER_GROQ:
        from .groq_provider import get_groq_provider

        client = get_groq_provider(model or settings.groq_default_model)
    elif provider == PROVIDER_LOCAL:
        from .ollama_provider import get_ollama_provider

        client = get_ollama_provider(model or settings.ollama_default_model)
    else:
        raise ValueError(
            f"Unknown LLM provider {provider!r}; expected one of "
            f"{', '.join(SUPPORTED_PROVIDERS)}"
        )

    if not client.is_available:
        raise RuntimeError(
            f"LLM provider {provider!r} is not available. "
            "Check GEMINI_API_KEY / GROQ_API_KEY (cloud) or the Ollama server (local)."
        )

    logger.info("[LLM] Resolved provider=%s model=%s", provider, client.model_name)
    return client


def get_llm_for_mode(
    mode: str | None = None,
    *,
    model: str | None = None,
) -> BaseLLMProvider:
    """Groq provider for ``cloud`` mode, Ollama for ``local`` mode.

    This is the default entry point for all pipeline call sites (Nodes 2-7).
    A ``local`` request that cannot reach Ollama raises; it never falls back to
    the cloud, because silently spending Groq/Gemini quota would defeat the
    point of running locally.
    """
    resolved = normalize_llm_mode(mode) if mode is not None else get_active_llm_mode()
    return get_llm_provider(
        PROVIDER_LOCAL if resolved == "local" else PROVIDER_GROQ,
        model=model,
    )


def get_cloud_llm(
    node: str,
    *,
    model: str | None = None,
    gemini_model: str | None = None,
) -> BaseLLMProvider:
    """Cloud-mode provider for a pipeline node, with Gemini reserved for Node 1.

    Node 1 (query orchestration) gets Gemini 2.5 Flash Lite when a
    ``GEMINI_API_KEY`` is configured: it is the cheapest and fastest-per-inference
    backend for a multi-iteration ReAct loop, and Node 1 runs serially at the
    head of every snapshot so it bounds total pipeline latency. Every other node
    gets Groq ``groq/compound``.

    Degrades loudly, never silently: without a Gemini key the request is served
    by Groq and the downgrade is logged. Local mode never calls this function.
    """
    settings = get_settings()
    if node == "query_orchestrator":
        if settings.gemini_api_key:
            try:
                return get_llm_provider(
                    PROVIDER_GEMINI, model=gemini_model or settings.gemini_default_model
                )
            except Exception as exc:
                logger.warning(
                    "[LLM] Gemini unavailable for node=%s (%s); using Groq",
                    node,
                    exc,
                )
        else:
            logger.warning(
                "[LLM] GEMINI_API_KEY not set; node=%s using Groq instead of Gemini",
                node,
            )
    return get_llm_provider(PROVIDER_GROQ, model=model)
