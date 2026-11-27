"""Numeric citations in the summary must reach the verifier as full citations.

The prompt tells the model to cite by menu number, so the summary carries
"stalls 5" and "officials 6". The verifier pattern only matches
"[Src: domain | Sent: X | verified]", so it extracts zero citations and the
Citation card reads 0%.

The converter that expands [1] into the canonical form exists but is never
called, and it indexes documents in arrival order while the prompt now ranks
verified documents first.
"""
from __future__ import annotations

import re

from app.services.nlp.narrative import LLMNarrativeClient
from app.services.verification.citation_verifier import CitationVerifier

SUMMARY = (
    "Vendors gathered outside the Baguio Public Market to denounce the "
    "proposed mallification that could displace their stalls 5. Community "
    "groups argue the PPP model favours private interests 1."
)


def _doc(i: int, verified: bool) -> dict:
    host = "verified" if verified else "unverified"
    return {
        "title": f"Baguio report {i}",
        "snippet": "Baguio City vendors reported concerns.",
        "url": f"https://{host}.example.com/{i}",
        "sentiment": "negative",
        "metadata": {
            "credibility_score": 0.9 if verified else 0.5,
            "tavily_verification_status": "verified" if verified else "unverified",
        },
    }


def _client() -> LLMNarrativeClient:
    return LLMNarrativeClient.__new__(LLMNarrativeClient)


def test_summary_citations_match_the_verifier_pattern() -> None:
    docs = [_doc(i, False) for i in range(20)] + [_doc(i, True) for i in range(10)]

    summary, _ = _client()._convert_citation_numbers(SUMMARY, [], docs)

    verifier = CitationVerifier.__new__(CitationVerifier)
    assert len(verifier.extract_citations(summary)) == 2, summary


def test_conversion_uses_the_verified_first_ranking() -> None:
    docs = [_doc(i, False) for i in range(20)] + [_doc(i, True) for i in range(10)]

    summary, _ = _client()._convert_citation_numbers(SUMMARY, [], docs)

    assert "| Verified]" in summary, summary
    assert "unverified.example.com" not in summary, summary


def test_citation_numbers_are_consumed() -> None:
    docs = [_doc(i, True) for i in range(10)]

    summary, _ = _client()._convert_citation_numbers(SUMMARY, [], docs)

    assert not re.search(r"\b[15]\b(?=\s*[.,])", summary), summary