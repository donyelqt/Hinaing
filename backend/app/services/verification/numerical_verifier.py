"""Numerical hallucination detection module.

Detects and verifies numerical claims in generated summaries to catch
fabricated statistics, numbers, and quantities.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class NumericalVerifier:
    """Detects and verifies numerical claims.

    Identifies hallucinated numbers by:
    1. Extracting all numerical values from claims
    2. Checking if numbers appear in source documents
    3. Allowing ±10% tolerance for approximate matches
    4. Flagging exact numbers without source support
    """

    # Match integers, decimals, and comma-separated numbers (e.g., 1,000 or 1.5M)
    NUMBER_PATTERN = re.compile(
        r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)([KMBkmb]?)\b'
    )

    # Number words to numeric mapping
    NUMBER_WORDS = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
        'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
        'eighteen': 18, 'nineteen': 18, 'twenty': 20, 'thirty': 30,
        'forty': 40, 'fifty': 50, 'hundred': 100, 'thousand': 1000,
        'million': 1_000_000, 'billion': 1_000_000_000,
    }

    def __init__(self, tolerance: float = 0.10):
        """Initialize numerical verifier.

        Args:
            tolerance: Acceptable deviation for number matching (default 10%)
        """
        self._tolerance = tolerance
        logger.info(f"[NumericalVerifier] Initialized with {tolerance:.0%} tolerance")

    def extract_numbers(self, text: str) -> list[dict[str, Any]]:
        """Extract all numbers from text with context.

        Args:
            text: Text to extract numbers from

        Returns:
            List of dicts with:
            - raw: Original number string
            - value: Numeric value (float)
            - position: Character position in text
            - suffix: K/M/B suffix if present
        """
        numbers = []

        # Extract numeric patterns
        for match in self.NUMBER_PATTERN.finditer(text):
            raw = match.group(1)
            suffix = match.group(2).upper()

            # Parse number (remove commas)
            try:
                value = float(raw.replace(',', ''))
            except ValueError:
                continue

            # Apply suffix multiplier
            multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000, '': 1}
            value *= multipliers.get(suffix, 1)

            numbers.append({
                "raw": match.group(0),
                "value": value,
                "position": match.start(),
                "suffix": suffix,
                "type": "numeric",
            })

        # Extract number words (simple implementation)
        words = text.lower().split()
        for i, word in enumerate(words):
            if word in self.NUMBER_WORDS:
                numbers.append({
                    "raw": word,
                    "value": float(self.NUMBER_WORDS[word]),
                    "position": text.lower().find(word),
                    "suffix": "",
                    "type": "word",
                })

        logger.info(f"[NumericalVerifier] Extracted {len(numbers)} numbers from text")
        return numbers

    def extract_numbers_from_documents(
        self,
        documents: list[dict[str, Any]]
    ) -> list[float]:
        """Extract all numbers from source documents.

        Args:
            documents: Source documents with 'snippet' or 'content'

        Returns:
            List of numeric values found in documents
        """
        all_numbers = []

        for doc in documents:
            # Get text content
            text = doc.get("snippet", "") or doc.get("content", "")
            if not text:
                continue

            # Extract numbers
            numbers = self.extract_numbers(text)
            all_numbers.extend(n["value"] for n in numbers)

        return all_numbers

    def verify_numerical_claim(
        self,
        claim: str,
        documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Verify numbers in claim match source documents.

        Args:
            claim: Claim text to verify
            documents: Source documents

        Returns:
            Verification result:
            - has_numbers: bool (whether claim contains numbers)
            - verified: bool (all numbers supported)
            - mismatches: List of unsupported numbers
            - hallucination_type: str | None
        """
        # Extract numbers from claim
        claim_numbers = self.extract_numbers(claim)

        if not claim_numbers:
            return {
                "has_numbers": False,
                "verified": True,
                "mismatches": [],
                "hallucination_type": None,
            }

        # Extract numbers from documents
        doc_numbers = self.extract_numbers_from_documents(documents)

        if not doc_numbers:
            # No numbers in documents = all claim numbers are hallucinated
            return {
                "has_numbers": True,
                "verified": False,
                "mismatches": [n["raw"] for n in claim_numbers],
                "hallucination_type": "numerical_hallucination",
            }

        # Check each claim number against document numbers
        mismatches = []
        for claim_num in claim_numbers:
            value = claim_num["value"]

            # Check for exact match or within tolerance
            is_supported = any(
                abs(doc_num - value) / max(doc_num, value, 1) <= self._tolerance
                for doc_num in doc_numbers
            )

            if not is_supported:
                mismatches.append(claim_num["raw"])

        is_verified = len(mismatches) == 0

        return {
            "has_numbers": True,
            "verified": is_verified,
            "mismatches": mismatches,
            "hallucination_type": "numerical_hallucination" if mismatches else None,
            "claim_numbers": [n["raw"] for n in claim_numbers],
            "tolerance_used": self._tolerance,
        }

    def verify_batch(
        self,
        claims: list[dict[str, Any]],
        documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Verify numerical claims in batch.

        Args:
            claims: List of claim dicts with 'claim' key
            documents: Source documents

        Returns:
            List of verification results (one per claim)
        """
        results = []

        for claim_dict in claims:
            claim_text = claim_dict.get("claim", "")
            result = self.verify_numerical_claim(claim_text, documents)
            result["claim"] = claim_text
            result["category"] = claim_dict.get("category", "General")
            results.append(result)

        return results


# Module-level singleton
_numerical_verifier_instance: NumericalVerifier | None = None


def get_numerical_verifier(tolerance: float = 0.10) -> NumericalVerifier:
    """Get or create singleton NumericalVerifier instance.

    Args:
        tolerance: Acceptable deviation for number matching (default 10%)

    Returns:
        Singleton NumericalVerifier instance
    """
    global _numerical_verifier_instance

    if _numerical_verifier_instance is None:
        _numerical_verifier_instance = NumericalVerifier(tolerance=tolerance)

    return _numerical_verifier_instance
