"""Regression test: the production theme path retries a zero-insight answer.

Guards the live 6h run where Infrastructure and Environment each returned
`{"insights": []}` once and were dropped, even though both had documents.
"""
from app.schemas.snapshot import WebDocument
from app.services.insights import nodes


class _LLM:
    model_name = "stub"

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0

    def generate_sync(self, **kwargs):
        self.calls += 1
        return self._replies.pop(0)


def _docs(count: int):
    return [
        WebDocument(
            title=f"Doc {i}",
            snippet="A Baguio infrastructure report.",
            url=f"https://example.gov/{i}",
        )
        for i in range(count)
    ]


def test_zero_insight_theme_is_retried(monkeypatch):
    llm = _LLM(['{"insights": []}', '{"insights": [{"title": "Fix drainage", "detail": "Clear the drain.", "evidence": ["https://example.gov/0"]}]}'])
    monkeypatch.setattr("app.services.llm.factory.get_llm_for_mode", lambda mode=None: llm)
    monkeypatch.setattr(
        "app.services.insights.nodes._build_theme_context", lambda docs: "ctx"
    )

    results = nodes._synthesize_single_theme("infrastructure", _docs(4), {})

    assert llm.calls == 2, llm.calls
    assert [r.title for r in results] == ["Fix drainage"]


def test_two_empty_attempts_drop_the_theme(monkeypatch):
    llm = _LLM(['{"insights": []}', '{"insights": []}'])
    monkeypatch.setattr("app.services.llm.factory.get_llm_for_mode", lambda mode=None: llm)
    monkeypatch.setattr(
        "app.services.insights.nodes._build_theme_context", lambda docs: "ctx"
    )

    results = nodes._synthesize_single_theme("environment", _docs(2), {})

    assert llm.calls == 2, llm.calls
    assert len(results) == 1
    assert results[0].evidence == []