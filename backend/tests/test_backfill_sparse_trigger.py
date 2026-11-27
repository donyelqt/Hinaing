"""A query that returns almost nothing must still get the Tavily safety net.

The trigger was \`if not web_docs\`, so a query returning 1 document never fired
the backfill. The live 2026-11-27 16:44 run got 1 per query and no backfill.

Two documents was the floor until the 20:14 run, where a two-document theme
produced an empty insight list and shipped a placeholder card. Three is the
floor now.
"""
from __future__ import annotations

import pytest

from app.schemas.snapshot import SnapshotRequest, WebDocument
from app.services.insights import agent_tools


def _doc(i: int) -> WebDocument:
    return WebDocument(
        title=f"Baguio report {i}",
        snippet="Baguio City",
        url=f"https://baguioheraldexpressonline.com/{i}",
    )


@pytest.mark.parametrize("count,expected", [(0, True), (1, True), (2, True), (5, False)])
def test_backfill_fires_on_sparse_results(count: int, expected: bool) -> None:
    request = SnapshotRequest(query="safety", platforms=["web"], focus_areas=["safety"])

    assert agent_tools._should_backfill([_doc(i) for i in range(count)]) is expected


def test_backfill_is_skipped_when_results_are_sufficient() -> None:
    request = SnapshotRequest(query="safety", platforms=["web"], focus_areas=["safety"])

    assert agent_tools._should_backfill([_doc(i) for i in range(10)]) is False