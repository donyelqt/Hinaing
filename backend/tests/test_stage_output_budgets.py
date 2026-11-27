"""The concurrent stage pair must fit the per-minute ceiling.

Sentiment and credibility run under one asyncio.gather in nodes.py, so their
budgets are spent in the same minute. The literals were 2000 and 4500, which
with prompts reached 8031 against an 8000 ceiling and returned 429.

The two constants are now 1500 and 3000. The pair reserves 4500 and leaves 3500
for prompts.
"""
from __future__ import annotations

from app.core.llm_budget import (
    LLM_CREDIBILITY_MAX_OUTPUT_TOKENS,
    LLM_FREE_TIER_TPM,
    LLM_SENTIMENT_MAX_OUTPUT_TOKENS,
)


def test_concurrent_pair_leaves_room_for_prompts() -> None:
    reserved = LLM_SENTIMENT_MAX_OUTPUT_TOKENS + LLM_CREDIBILITY_MAX_OUTPUT_TOKENS

    assert reserved <= LLM_FREE_TIER_TPM / 2, reserved


def test_each_stage_fits_alone() -> None:
    assert LLM_SENTIMENT_MAX_OUTPUT_TOKENS < LLM_FREE_TIER_TPM
    assert LLM_CREDIBILITY_MAX_OUTPUT_TOKENS < LLM_FREE_TIER_TPM