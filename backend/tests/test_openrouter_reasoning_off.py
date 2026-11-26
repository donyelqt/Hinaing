"""Regression test: OpenRouter JSON stages disable reasoning.

Nemotron defaults to ``reasoning.effort: high`` on OpenRouter, and reasoning
tokens count against ``max_tokens``. A long claim array was cut mid-string and
parsed as zero claims. The provider must send ``reasoning.effort: none`` so the
whole output budget reaches the JSON.

Groq is untouched: it has no such parameter and keeps its own provider.
"""
import asyncio

from app.services.llm.openrouter_provider import OpenRouterProvider


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _Client:
    def __init__(self, payload):
        self._payload = payload
        self.sent: list[dict] = []

    async def post(self, path, json=None):
        self.sent.append(json)
        return _Response(self._payload)


def _provider(client) -> OpenRouterProvider:
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider._model = "nvidia/nemotron-3-ultra-550b-a55b:free"
    provider._api_key = "test-key"
    provider._max_retries = 0
    provider._async_clients = {}
    provider._sync_client = client
    provider._get_async_client = lambda: client  # type: ignore[assignment]
    return provider


def test_async_generate_disables_reasoning():
    client = _Client({"choices": [{"message": {"content": "[]"}}]})
    provider = _provider(client)

    asyncio.run(provider.generate(prompt="p", max_tokens=6000))

    assert client.sent[0]["reasoning"] == {"effort": "none"}


def test_sync_generate_disables_reasoning():
    class _SyncClient:
        def __init__(self):
            self.sent = []

        def post(self, path, json=None):
            self.sent.append(json)
            return _Response({"choices": [{"message": {"content": "[]"}}]})

    client = _SyncClient()
    provider = _provider(client)

    provider.generate_sync(prompt="p", max_tokens=6000)

    assert client.sent[0]["reasoning"] == {"effort": "none"}


def test_caller_kwargs_still_win():
    client = _Client({"choices": [{"message": {"content": "[]"}}]})
    provider = _provider(client)

    asyncio.run(
        provider.generate(prompt="p", max_tokens=6000, reasoning={"effort": "high"})
    )

    assert client.sent[0]["reasoning"] == {"effort": "high"}