"""Ollama LLM provider for local model inference.

Supports Qwen 2.5 1.5B / 3B and other Ollama-served models.
Uses Ollama's native /api/chat endpoint (http://localhost:11434).

Ollama 0.13+ dropped the OpenAI-compatible /v1 endpoint, so we
talk to the native API directly via httpx.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, AsyncIterator

import httpx

from ...core.config import get_settings
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Global semaphore to limit concurrent Ollama requests
_OLLAMA_CONCURRENCY_LIMIT = asyncio.Semaphore(10)


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider for local model inference.

    Talks to Ollama's native /api/chat endpoint. Ollama 0.13+ removed
    the OpenAI-compatible /v1 endpoint, so we use the native API directly.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        *,
        model: str = "qwen2.5:3b",
        base_url: str | None = None,
        timeout: float = 180.0,
        max_retries: int = 3,
    ):
        """Initialize Ollama provider.

        Args:
            model: Ollama model name (e.g. qwen2.5:3b, qwen2.5:1.5b)
            base_url: Ollama server URL (defaults to localhost:11434)
            timeout: Request timeout in seconds (local models are slower)
            max_retries: Number of retry attempts on failure
        """
        settings = get_settings()
        self._model = model
        self._base_url = (
            (base_url or getattr(settings, "ollama_base_url", self.DEFAULT_BASE_URL))
        ).rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        logger.info(
            f"[Ollama] Initialized with model: {model} "
            f"(base_url: {self._base_url})"
        )

    @property
    def is_available(self) -> bool:
        """Check if Ollama client is configured."""
        return self._client is not None

    @property
    def model_name(self) -> str:
        """Get current model name."""
        return self._model

    async def _chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Send a chat request to Ollama's native /api/chat endpoint."""
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    f"[Ollama] Attempt {attempt}/{self._max_retries} failed: {exc}"
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)

        raise RuntimeError(
            f"[Ollama] Generation failed after {self._max_retries} retries: {last_exc}"
        )

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        """Generate text with local Ollama model.

        Expected latency: 30-120s for 1000 tokens on CPU.
        Uses global semaphore to prevent connection pool exhaustion.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with _OLLAMA_CONCURRENCY_LIMIT:
            data = await self._chat(
                messages, temperature=temperature, max_tokens=max_tokens
            )

        content = data.get("message", {}).get("content", "")
        return content

    async def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream generation from Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with _OLLAMA_CONCURRENCY_LIMIT:
            payload = {
                "model": self._model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            async with self._client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate JSON response from Ollama."""
        raw = await self.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Parse JSON from model response with robust error handling."""
        raw = raw.strip()

        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try extracting from code fences
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding first { or [
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = raw.find(start_char)
            if start == -1:
                continue
            end = raw.rfind(end_char)
            if end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    continue

        logger.warning(f"[Ollama] Could not parse JSON from response: {raw[:200]}")
        return {}


# Cache of provider instances per model (prevents singleton pollution)
_ollama_providers: dict[str, OllamaProvider] = {}
_provider_lock = __import__("threading").Lock()


def get_ollama_provider(model: str = "qwen2.5:3b") -> OllamaProvider:
    """Get or create Ollama provider instance for specific model."""
    global _ollama_providers
    with _provider_lock:
        if model not in _ollama_providers:
            _ollama_providers[model] = OllamaProvider(model=model)
        return _ollama_providers[model]


def clear_ollama_cache():
    """Clear all cached Ollama provider instances."""
    global _ollama_providers
    with _provider_lock:
        _ollama_providers.clear()
        logger.info("[Ollama] Cleared all provider instances")