"""Two distinct articles that share a 50-character opening must both survive.

The title rule truncated to 50 characters, so any two headlines with the same
opening produced the same key and the second was dropped as a duplicate.
"""
from __future__ import annotations

from app.schemas.snapshot import WebDocument
from app.services.insights.agent_tools import deduplicate_documents


def _doc(url: str, title: str) -> WebDocument:
    return WebDocument(title=title, snippet="Baguio City", url=url)


def test_articles_sharing_a_50_char_prefix_are_both_kept() -> None:
    docs = [
        _doc("https://baguioheraldexpressonline.com/a", "Baguio City fire incident reported in Session Road area"),
        _doc("https://baguioheraldexpressonline.com/b", "Baguio City fire incident reported in Session Road area near market"),
        _doc("https://baguioheraldexpressonline.com/c", "Baguio City fire incident reported in Session Road area at night"),
    ]

    kept = deduplicate_documents(docs)

    assert [doc.url for doc in kept] == [doc.url for doc in docs]


def test_identical_titles_on_different_urls_are_both_kept() -> None:
    docs = [
        _doc("https://baguioheraldexpressonline.com/a", "Baguio City water shortage deepens"),
        _doc("https://baguio.bomboradyo.com/b", "Baguio City water shortage deepens"),
    ]

    kept = deduplicate_documents(docs)

    assert len(kept) == 2


def test_a_short_title_is_not_matched_against_a_longer_one() -> None:
    docs = [
        _doc("https://baguioheraldexpressonline.com/a", "Baguio fire"),
        _doc("https://baguioheraldexpressonline.com/b", "Baguio fire spreads to three barangays"),
    ]

    kept = deduplicate_documents(docs)

    assert len(kept) == 2