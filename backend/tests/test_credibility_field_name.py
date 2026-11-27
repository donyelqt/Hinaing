"""The chat payload must carry the field the card reads.

The frontend reads ``credibility.review_percent``. The backend emitted
``low_percent``. The card rendered ``undefined%`` because the key was absent.
"""
from __future__ import annotations

from app.routers.chat_analyze import _credibility_breakdown


def test_breakdown_emits_the_field_the_card_reads() -> None:
    breakdown = _credibility_breakdown(3, 4, 0.69)

    assert "review_percent" in breakdown
    assert breakdown["review_percent"] == 25


def test_breakdown_still_sums_to_one_hundred() -> None:
    breakdown = _credibility_breakdown(17, 40, 0.5)

    assert breakdown["high_percent"] + breakdown["review_percent"] == 100


def test_breakdown_keeps_avg_score_and_high_percent() -> None:
    breakdown = _credibility_breakdown(0, 4, 0.91)

    assert breakdown["avg_score"] == 91
    assert breakdown["high_percent"] == 0
    assert breakdown["review_percent"] == 100