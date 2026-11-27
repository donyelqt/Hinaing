"""Every configured theme reaches the narrative, and verified docs lead.

A flat slice of theme insights drops whole themes when any theme emits more
insights than the cap allows. Six themes at five insights each is 30 lines, and
the first 9 are two categories.

The document cap is also a flat slice, so a run whose verified documents arrive
last shows the model 15 unverified ones.
"""
from __future__ import annotations

from app.services.nlp.narrative import (
    NARRATIVE_DOC_LIMIT,
    NARRATIVE_THEME_INSIGHT_LIMIT,
    LLMNarrativeClient,
)

CATEGORIES = [
    "Infrastructure",
    "Health & Wellness",
    "Public Safety",
    "Tourism & Events",
    "Business & Economy",
    "Environment",
]


def _themes(per_category: int) -> list[dict]:
    return [
        {"category": cat, "title": f"Recommendation {i} for Baguio City", "detail": "detail"}
        for cat in CATEGORIES
        for i in range(per_category)
    ]


def _doc(i: int, verified: bool) -> dict:
    host = "verified" if verified else "unverified"
    return {
        "title": f"Baguio report {i}",
        "snippet": "Baguio City officials reported concerns. " * 2,
        "url": f"https://{host}.example.com/{i}",
        "sentiment": "negative",
        "metadata": {
            "credibility_score": 0.9 if verified else 0.5,
            "tavily_verification_status": "verified" if verified else "unverified",
        },
    }


def _prompt(themes: list[dict], docs: list[dict]) -> str:
    client = LLMNarrativeClient.__new__(LLMNarrativeClient)
    return client._build_prompt(
        window="6h",
        focus_areas=CATEGORIES,
        documents=docs,
        theme_insights=themes,
        sentiment_distribution={"negative": 1.0},
    )


def _carried_categories(prompt: str) -> list[str]:
    seen: list[str] = []
    for line in prompt.splitlines():
        if line.startswith("THEME ["):
            cat = line.split("[", 1)[1].split("]", 1)[0]
            if cat not in seen:
                seen.append(cat)
    return seen


def test_every_theme_survives_the_cap() -> None:
    prompt = _prompt(_themes(5), [])

    assert _carried_categories(prompt) == CATEGORIES


def test_cap_is_not_exceeded() -> None:
    prompt = _prompt(_themes(5), [])

    carried = sum(1 for line in prompt.splitlines() if line.startswith("THEME ["))

    assert carried <= NARRATIVE_THEME_INSIGHT_LIMIT


def test_verified_documents_lead_the_menu() -> None:
    docs = [_doc(i, False) for i in range(50)] + [_doc(i, True) for i in range(14)]

    prompt = _prompt([], docs)

    menu = [line for line in prompt.splitlines() if line.startswith("[")]
    assert len(menu) == NARRATIVE_DOC_LIMIT
    assert all("| verified |" in line for line in menu[:-1]), menu[:3]