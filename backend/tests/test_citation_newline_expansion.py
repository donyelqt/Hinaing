"""A citation at the end of a line inside a multi-paragraph summary must expand.

The narrative writes one citation per sentence and separates paragraphs with a
blank line. The converter regex required the number to sit at the end of the
whole string, so only the last paragraph converted. The live run expanded 1 of
12 numbers and the verifier saw 1 citation.
"""
from __future__ import annotations

import re

from app.services.nlp.narrative import LLMNarrativeClient
from app.services.verification.citation_verifier import CitationVerifier

SUMMARY = (
    "Infrastructure: power outages 1\n\n"
    "Business & Economy: rent hikes 4\n\n"
    "Health: dengue cases 6\n\n"
    "Conclusion: outlook 10"
)


def _docs() -> list[dict]:
    return [
        {
            "title": f"Doc {i}",
            "snippet": "x",
            "url": f"https://host{i}.example.com/{i}",
            "sentiment": "negative",
            "metadata": {"credibility_score": 0.8, "tavily_verification_status": "verified"},
        }
        for i in range(1, 16)
    ]


def test_every_paragraph_citation_expands() -> None:
    client = LLMNarrativeClient.__new__(LLMNarrativeClient)

    summary, _ = client._convert_citation_numbers(SUMMARY, [], _docs())

    verifier = CitationVerifier.__new__(CitationVerifier)
    assert len(verifier.extract_citations(summary)) == 4, summary


def test_no_bare_number_is_left_at_a_line_end() -> None:
    client = LLMNarrativeClient.__new__(LLMNarrativeClient)

    summary, _ = client._convert_citation_numbers(SUMMARY, [], _docs())

    assert not re.search(r"\s\d{1,2}\s*$", summary, re.MULTILINE), summary