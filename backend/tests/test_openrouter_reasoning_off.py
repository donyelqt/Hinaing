"""Regression test: OpenRouter disables reasoning so JSON stages keep their budget.

Nemotron defaults to ``reasoning.effort: high`` on OpenRouter, and reasoning
tokens count against ``max_tokens``. A claim array was cut mid-string and
parsed as zero claims. The payload the API receives must ask for no reasoning.
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


class _AsyncClient:
    def __init__(self):
        self.sent: list[dict] = []

    async def post(self, path, json=None):
        self.sent.append(json)
        return _Response({"choices": [{"message": {"content": "[]"}}]})


class _SyncClient(_AsyncClient):
    def post(self, path, json=None):  # type: ignore[override]
        self.sent.append(json)
        return _Response({"choices": [{"message": {"content": "[]"}}]})


def _provider(async_client, sync_client) -> OpenRouterProvider:
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider._model = "nvidia/nemotron-3-ultra-550b-a55b:free"
    provider._api_key = "test-key"
    provider._max_retries = 0
    provider._async_clients = {}
    provider._sync_client = sync_client
    provider._get_async_client = lambda: async_client  # type: ignore[assignment]
    return provider


def test_async_generate_sends_no_reasoning():
    client = _AsyncClient()
    provider = _provider(client, _SyncClient())

    asyncio.run(provider.generate(prompt="p", max_tokens=6000))

    assert client.sent[0]["reasoning"] == {"effort": "none"}


def test_sync_generate_sends_no_reasoning():
    client = _SyncClient()
    provider = _provider(_AsyncClient(), client)

    provider.generate_sync(prompt="p", max_tokens=6000)

    assert client.sent[0]["reasoning"] == {"effort": "none"}


def test_caller_reasoning_override_is_kept():
    client = _AsyncClient()
    provider = _provider(client, _SyncClient())

    asyncio.run(
        provider.generate(prompt="p", max_tokens=6000, reasoning={"effort": "high"})
    )

    assert client.sent[0]["reasoning"] == {"effort": "high"}