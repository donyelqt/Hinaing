"""A prose answer must still yield a summary, and the raw text must be logged.

The 22:22 run returned 200 with text the parser could not use, and the log said
only "returned no summary". Three paths produce that: prose with no summary key,
a JSON object with an empty summary, and a JSON object with insights only.

The raw text is now logged when parsing fails, and a prose fallback returns the
text as the summary instead of an empty string.
"""
from __future__ import annotations

from app.services.nlp.narrative import LLMNarrativeClient


def test_prose_without_json_returns_the_text_as_summary() -> None:
    prose = "Public Safety: fire incidents fell 7. Infrastructure: water 5."

    result = LLMNarrativeClient._try_parse_json(prose)

    assert result is not None
    assert "fire incidents fell" in result["summary"]


def test_empty_summary_still_reads_as_empty() -> None:
    result = LLMNarrativeClient._try_parse_json('{"summary": "", "insights": []}')

    assert result is not None
    assert result["summary"] == ""


def test_json_with_insights_only_has_no_summary() -> None:
    result = LLMNarrativeClient._try_parse_json('{"insights": [{"category": "x"}]}')

    assert result is not None
    assert result.get("summary", "") == ""