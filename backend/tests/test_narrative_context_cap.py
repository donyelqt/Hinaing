"""The narrative prompt must leave room for its own output.

The provider counts prompt plus max_tokens against an 8000 per-minute
allowance. The narrative prompt carried 30 documents and 18 theme insights,
which measured 5413 tokens. With the 4000 output budget that is 9413, so the
coordinator returned 413 and the run shipped no summary.

Two documents and their insight lines are still carried, so the cap must cut
volume, not evidence.
"""
from __future__ import annotations

from app.services.nlp.narrative import LLMNarrativeClient


def _doc(i: int) -> dict:
    return {
        "title": f"Baguio City civic report number {i} on infrastructure and health",
        "snippet": "Baguio City officials reported rising concerns across barangays. " * 2,
        "url": f"https://newsinfo.inquirer.net/{i}",
        "sentiment": "negative",
        "metadata": {"credibility_score": 0.74},
    }


def _themes(n: int) -> list[dict]:
    return [
        {
            "category": "Infrastructure",
            "title": f"Actionable recommendation {i} for Baguio City government",
            "detail": "Implement temporary traffic diversion plans and deploy additional enforcers.",
        }
        for i in range(n)
    ]


def _prompt(doc_count: int, theme_count: int) -> str:
    client = LLMNarrativeClient.__new__(LLMNarrativeClient)
    return client._build_prompt(
        window="6h",
        focus_areas=["infrastructure", "environment", "economy", "health", "safety", "tourism"],
        documents=[_doc(i) for i in range(doc_count)],
        theme_insights=_themes(theme_count),
        sentiment_distribution={"negative": 0.59, "neutral": 0.25, "positive": 0.16},
    )


def test_narrative_prompt_leaves_room_for_its_output() -> None:
    from app.core.llm_budget import LLM_FREE_TIER_TPM, LLM_MAX_OUTPUT_TOKENS

    prompt = _prompt(30, 18)
    approx_tokens = len(prompt) // 4

    assert approx_tokens + LLM_MAX_OUTPUT_TOKENS <= LLM_FREE_TIER_TPM, (
        f"prompt {approx_tokens} + budget {LLM_MAX_OUTPUT_TOKENS} exceeds "
        f"{LLM_FREE_TIER_TPM}"
    )


def test_narrative_still_carries_documents_and_insights() -> None:
    prompt = _prompt(30, 18)

    assert "SUPPORTING CONVERSATIONS" in prompt
    assert "PRE-ANALYZED THEME INSIGHTS" in prompt
    assert "newsinfo.inquirer.net" in prompt