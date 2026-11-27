"""Credibility and Review must sum to 100 for every document count.

The backend rounded each share independently. At 17 verified of 40 documents
that produced 42 and 57, which sums to 99. The sentiment page rounds once and
subtracts, so the same run showed 42 and 58.
"""
from __future__ import annotations

import pytest

from app.routers.chat_analyze import _credibility_breakdown


@pytest.mark.parametrize("verified,total", [(17, 40), (23, 40), (0, 3), (3, 3), (1, 8)])
def test_shares_sum_to_one_hundred(verified: int, total: int) -> None:
    breakdown = _credibility_breakdown(verified, total, 0.5)

    assert breakdown["high_percent"] + breakdown["review_percent"] == 100


def test_review_is_the_rounded_complement_of_verified() -> None:
    breakdown = _credibility_breakdown(17, 40, 0.5)

    assert breakdown["high_percent"] == 42
    assert breakdown["review_percent"] == 58


def test_avg_score_is_the_five_signal_mean() -> None:
    breakdown = _credibility_breakdown(0, 4, 0.91)

    assert breakdown["avg_score"] == 91
    assert breakdown["high_percent"] == 0
    assert breakdown["review_percent"] == 100