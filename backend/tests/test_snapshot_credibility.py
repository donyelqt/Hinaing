"""The snapshot payload must carry the credibility card values.

The sentiment page reads snapshot.credibility, but only the chat formatter ever
built that object, so the card was hidden. The snapshot endpoint returns the raw
SnapshotResponse, which had no such field.

The values come from the same enriched documents the chat formatter uses, over
one denominator, so the two pages cannot disagree.
"""
from __future__ import annotations

from app.schemas.snapshot import SnapshotResponse, WebDocument
from app.services.insights.nodes import _credibility_breakdown, _snapshot_credibility

def _doc(status: str | None, score: float | None) -> WebDocument:
    metadata: dict = {}
    if status is not None:
        metadata["tavily_verification_status"] = status
    if score is not None:
        metadata["credibility_score"] = score
    return WebDocument(title="Baguio report", snippet="Baguio City", metadata=metadata)


def _snapshot(docs: list[WebDocument]) -> SnapshotResponse:
    snapshot = SnapshotResponse(
        overall_sentiment={"label": "Concerned", "summary": "Summary.", "scores": {"negative": 0.6, "neutral": 0.2, "positive": 0.2}},
        actionable_insights=[],
        sources=docs,
    )
    snapshot.credibility = _snapshot_credibility(docs)
    return snapshot


def test_snapshot_carries_the_credibility_card_values() -> None:
    snapshot = _snapshot([_doc("verified", 0.9), _doc("unverified", 0.5)])

    assert snapshot.credibility is not None
    assert snapshot.credibility.high_percent == 50
    assert snapshot.credibility.review_percent == 50
    assert snapshot.credibility.avg_score == 70


def test_snapshot_credibility_is_none_without_documents() -> None:
    assert _snapshot([]).credibility is None


def test_breakdown_rounds_the_complement_not_the_raw_share() -> None:
    breakdown = _credibility_breakdown(verified=1, total=3, avg_score=0.5)

    assert breakdown["high_percent"] == 33
    assert breakdown["review_percent"] == 67
    assert breakdown["high_percent"] + breakdown["review_percent"] == 100