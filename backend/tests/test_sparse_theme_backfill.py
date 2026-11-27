"""A theme with two documents must reach the backfill.

LangSearch returned two documents for the infrastructure query. The sparse
threshold is two, so the backfill never fired, the theme agent answered with an
empty insight list, and the run shipped a placeholder card instead of evidence.

One document cannot express a disagreement, and two is the same shape. The
threshold must be three so a theme with fewer than three reaches Tavily.
"""
from __future__ import annotations

from app.schemas.snapshot import SnapshotRequest, WebDocument
from app.services.insights import agent_tools


def _doc(i: int) -> WebDocument:
    return WebDocument(
        title=f"Baguio traffic report {i}",
        snippet="Baguio City",
        url=f"https://baguioheraldexpressonline.com/{i}",
    )


def test_two_documents_are_sparse() -> None:
    assert agent_tools._should_backfill([_doc(0), _doc(1)]) is True


def test_three_documents_are_enough() -> None:
    docs = [_doc(0), _doc(1), _doc(2)]

    assert agent_tools._should_backfill(docs) is False


def test_empty_result_is_sparse() -> None:
    assert agent_tools._should_backfill([]) is True