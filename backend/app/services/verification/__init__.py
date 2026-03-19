"""Verification module for claim faithfulness checking.

This module provides NLI-based claim verification:
- ClaimExtractor: Extracts claims from generated summaries
- EntailmentChecker: Checks if claims are entailed by source documents
"""

from .claim_extractor import ClaimExtractor
from .entailment_checker import EntailmentChecker

__all__ = ["ClaimExtractor", "EntailmentChecker"]
