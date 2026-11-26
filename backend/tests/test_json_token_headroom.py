"""Regression test: JSON-producing stages request reasoning headroom.

Guards the OpenRouter run where a 4000-token cap truncated a reasoning
model's JSON mid-string, in both claim extraction and theme synthesis.
"""
import asyncio

from app.core.llm_budget import (
    LLM_CLAIM_MAX_OUTPUT_TOKENS,
    LLM_FREE_TIER_TPM,
    LLM_MAX_OUTPUT_TOKENS,
)
from app.services.verification.claim_extractor import ClaimExtractor


class _LLM:
    def __init__(self, reply):
        self._reply = reply
        self.requested: int | None = None

    async def generate(self, **kwargs):
        self.requested = kwargs.get("max_tokens")
        return self._reply


def test_claim_extractor_requests_reasoning_headroom():
    llm = _LLM('[{"claim": "Fire incidents rose amid El Nino", "category": "Public Safety"}]')
    extractor = ClaimExtractor.__new__(ClaimExtractor)
    extractor._model_name = "stub"
    extractor._resolve_model = lambda mode=None: llm  # type: ignore[assignment]

    asyncio.run(extractor.extract_claims("A summary long enough to analyse."))

    assert llm.requested == LLM_CLAIM_MAX_OUTPUT_TOKENS
    assert llm.requested > LLM_MAX_OUTPUT_TOKENS


def test_json_budget_fits_the_free_tier():
    assert LLM_CLAIM_MAX_OUTPUT_TOKENS <= LLM_FREE_TIER_TPM