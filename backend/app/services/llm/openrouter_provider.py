"""OpenRouter LLM provider.

Single gateway for the whole pipeline. Routes requests to OpenRouter's
OpenAI-compatible chat completions API. Default model is ``nvidia/nemotron-3-ultra-550b-a55b:free``;
the gateway carries the whole pipeline so one API key runs every node.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from typing import Any, AsyncIterator

import httpx
from ...core.config import get_settings
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Global semaphore limits concurrent OpenRouter API requests.
_OPENROUTER_CONCURRENCY_LIMIT = asyncio.Semaphore(15)

_DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider with the same surface as GroqProvider.

    Async clients are cached per event loop so that thread-local loops
    created by ``asyncio.new_event_loop()`` in the credibility and
    sentiment agents never share a stale transport. The sync client is
    a plain ``httpx.Client`` with no loop binding.
    """

    def __init__(
        self,
        *,
        model: str = _DEFAULT_MODEL,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

        self._sync_client: httpx.Client | None = None
        # Per-loop async clients: maps id(loop) -> (loop_ref, client)
        self._async_clients: dict[int, tuple[Any, httpx.AsyncClient]] = {}
        self._async_lock = threading.Lock()

        if self._api_key:
            self._sync_client = httpx.Client(
                base_url=_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hinaing.app",
                    "X-Title": "Hinaing Civic Analysis",
                },
                timeout=httpx.Timeout(timeout, connect=10.0),
            )
            logger.info(f"[OpenRouter] Initialized with model: {model}")
        else:
            logger.warning("[OpenRouter] API key not configured")

    # ------------------------------------------------------------------
    # BaseLLMProvider interface
    # ------------------------------------------------------------------
    @property
    def is_available(self) -> bool:
        return self._api_key is not None

    @property
    def model_name(self) -> str:
        return self._model

    def _get_async_client(self) -> httpx.AsyncClient:
        """Return an AsyncClient bound to the current running event loop.

        Thread-local loops created by ``asyncio.new_event_loop()`` in the
        credibility and sentiment agents are short-lived. A client cached
        from a closed loop would hold a dead transport, producing the
        ``TCPTransport closed=True`` failures this cache exists to prevent.
        Entries are matched by loop identity, never by ``id()`` alone,
        because CPython reuses ids after garbage collection.
        """
        loop = asyncio.get_running_loop()
        with self._async_lock:
            for stored_loop, client in list(self._async_clients.values()):
                if stored_loop is not loop and stored_loop.is_closed():
                    del self._async_clients[id(stored_loop)]
            for stored_loop, client in self._async_clients.values():
                if stored_loop is loop:
                    return client
            client = httpx.AsyncClient(
                base_url=_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hinaing.app",
                    "X-Title": "Hinaing Civic Analysis",
                },
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30.0,
                ),
                timeout=httpx.Timeout(self._timeout, connect=10.0),
            )
            self._async_clients[id(loop)] = (loop, client)
            return client

    def _build_payload(self, prompt, system_prompt, temperature, max_tokens, stream, **kwargs):
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        if not self._api_key:
            raise RuntimeError("[OpenRouter] Client not initialized (missing API key)")

        client = self._get_async_client()
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens, stream=False, **kwargs)
        async with _OPENROUTER_CONCURRENCY_LIMIT:
            last_exc: Exception | None = None
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.post("/chat/completions", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
                except Exception as exc:
                    last_exc = exc
                    logger.warning(f"[OpenRouter] Attempt {attempt + 1}/{self._max_retries + 1} failed: {exc}")
                    await asyncio.sleep(2 ** attempt)
            logger.error(f"[OpenRouter] Generation failed after {self._max_retries + 1} attempts: {last_exc}")
            assert last_exc is not None
            raise last_exc

    async def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        if not self._api_key:
            raise RuntimeError("[OpenRouter] Client not initialized (missing API key)")

        client = self._get_async_client()
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens, stream=True, **kwargs)
        try:
            async with client.stream("POST", "/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    line = line[5:].strip()
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]
        except Exception as exc:
            logger.error(f"[OpenRouter] Streaming failed: {exc}")
            raise

    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        **kwargs,
    ) -> dict[str, Any]:
        json_prompt = f"""{prompt}

Respond with ONLY valid JSON. No markdown formatting, no explanations."""
        raw = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return self._parse_json(raw)

    def generate_sync(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        if not self._sync_client:
            raise RuntimeError("[OpenRouter] Sync client not initialized (missing API key)")

        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens, stream=False, **kwargs)
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._sync_client.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
                return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
            except Exception as exc:
                last_exc = exc
                logger.warning(f"[OpenRouter] Sync attempt {attempt + 1}/{self._max_retries + 1} failed: {exc}")
                import time as _time
                _time.sleep(2 ** attempt)
        logger.error(f"[OpenRouter] Sync generation failed after {self._max_retries + 1} attempts: {last_exc}")
        assert last_exc is not None
        raise last_exc

    # ------------------------------------------------------------------
    # JSON parsing (mirrors GroqProvider behavior)
    # ------------------------------------------------------------------
    def _parse_json(self, raw: str) -> dict[str, Any]:
        text = raw.strip()
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if json_match:
            text = json_match.group(1).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(re.sub(r",\s*([}\]])", r"\1", text))
        except json.JSONDecodeError:
            pass
        depth = 0
        last_valid = -1
        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    last_valid = i
                    break
        if last_valid != -1:
            try:
                return json.loads(text[: last_valid + 1])
            except json.JSONDecodeError:
                pass
        logger.warning(f"[OpenRouter] Failed to parse JSON: {text[:200]}...")
        return {}


_openrouter_provider: OpenRouterProvider | None = None


def get_openrouter_provider(model: str | None = None) -> OpenRouterProvider:
    global _openrouter_provider
    settings = get_settings()
    target = model or settings.openrouter_default_model
    if (
        _openrouter_provider is None
        or _openrouter_provider.model_name != target
    ):
        _openrouter_provider = OpenRouterProvider(
            model=target,
            timeout=settings.openrouter_timeout,
            max_retries=settings.openrouter_max_retries,
        )
    return _openrouter_provider