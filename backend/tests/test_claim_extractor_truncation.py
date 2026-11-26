"""Regression test: claim extraction retries a truncated JSON response.

Guards the OpenRouter run where nemotron returned a JSON array cut
mid-string, the parse returned zero claims, and faithfulness reported 0/0.
"""
import asyncio

from app.services.verification.claim_extractor import ClaimExtractor


class _LLM:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0

    async def generate(self, **kwargs):
        self.calls += 1
        return self._replies.pop(0)


def _extractor(replies) -> ClaimExtractor:
    llm = _LLM(replies)
    extractor = ClaimExtractor.__new__(ClaimExtractor)
    extractor._model_name = "stub"
    extractor._resolve_model = lambda mode=None: llm  # type: ignore[assignment]
    extractor._llm = llm  # type: ignore[attr-defined]
    return extractor


def test_truncated_response_is_retried():
    truncated = '[{"claim": "SM City Baguio planted 596,055 trees", "category": "Environment"}, {"claim": "Fire incidents rose amid El Nin'
    good = '[{"claim": "Fire incidents rose amid El Nino", "category": "Public Safety"}]'
    extractor = _extractor([truncated, good])

    claims = asyncio.run(extractor.extract_claims("A summary long enough to analyse."))

    assert [c["claim"] for c in claims] == ["Fire incidents rose amid El Nino"]


def test_two_truncated_attempts_return_no_claims():
    truncated = '[{"claim": "cut mid-string'
    extractor = _extractor([truncated] * 5)

    claims = asyncio.run(extractor.extract_claims("A summary long enough to analyse."))

    assert claims == []
    assert extractor._llm.calls == 5, extractor._llm.calls


def test_valid_response_is_not_retried():
    good = '[{"claim": "Fire incidents rose amid El Nino", "category": "Public Safety"}]'
    extractor = _extractor([good])

    claims = asyncio.run(extractor.extract_claims("A summary long enough to analyse."))

    assert len(claims) == 1
    assert extractor._llm.calls == 1