"""Two ordinary sentences must not read as fabricated statistics.

The 20:34 run flagged "over 000 mature marijuana plants" and "Two individuals
were arrested". Neither is a hallucinated number.

"000" is what remains when a thousands separator is lost upstream. It has no
significant digit, so it is an extraction artifact, not a claim.

"two" is prose. The verifier mapped every number word to a value, so a spelled
count with no digits in the documents was flagged. Only a word carrying a
magnitude is a quantity.
"""
from __future__ import annotations

from app.services.verification.numerical_verifier import NumericalVerifier


def _verify(claim: str, documents: list[dict]) -> dict:
    return NumericalVerifier().verify_numerical_claim(claim, documents)


def test_leading_zero_artifact_is_not_a_number() -> None:
    claim = "Operations eradicated over 000 mature marijuana plants."
    docs = [{"snippet": "PDEA agents eradicated 7,000 mature marijuana plants in Benguet."}]

    result = _verify(claim, docs)

    assert result["mismatches"] == []
    assert result["verified"] is True


def test_spelled_count_without_magnitude_is_prose() -> None:
    claim = "Two individuals were arrested for illegal logging in Apayao."
    docs = [{"snippet": "Apayao authorities arrested illegal logging suspects."}]

    result = _verify(claim, docs)

    assert result["mismatches"] == []
    assert result["verified"] is True


def test_spelled_magnitude_is_still_a_quantity() -> None:
    claim = "The council approved two thousand pesos for each household."
    docs = [{"snippet": "The council approved 2,000 pesos per household."}]

    assert _verify(claim, docs)["verified"] is True


def test_a_real_fabricated_statistic_is_still_caught() -> None:
    claim = "The program planted 596,055 trees since June."
    docs = [{"snippet": "The program planted 5,000 trees since June."}]

    result = _verify(claim, docs)

    assert result["verified"] is False
    assert "596,055" in result["mismatches"]


def test_trailing_citation_number_is_not_a_quantity() -> None:
    claim = "Operations eradicated over 7,000 mature marijuana plants 6."
    docs = [{"snippet": "PDEA agents eradicated 7,000 mature marijuana plants."}]

    result = _verify(claim, docs)

    assert result["mismatches"] == []
    assert result["verified"] is True


def test_a_number_inside_the_sentence_is_still_a_quantity() -> None:
    claim = "The program planted 596,055 trees 3."
    docs = [{"snippet": "The program planted 5,000 trees."}]

    result = _verify(claim, docs)

    assert result["verified"] is False
    assert "596,055" in result["mismatches"]