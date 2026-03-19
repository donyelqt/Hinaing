"""Faithfulness Agent for claim verification.

Combines claim extraction and entailment checking to verify generated summaries.
"""
from __future__ import annotations

import logging
from typing import Any

from ..verification.claim_extractor import ClaimExtractor
from ..verification.entailment_checker import EntailmentChecker

logger = logging.getLogger(__name__)


class FaithfulnessAgent:
    """Verifies claim faithfulness in generated summaries.
    
    Uses Sequential Pipeline Pattern:
    1. Extract claims from summary (ClaimExtractor)
    2. Verify claims against documents (EntailmentChecker)
    3. Report faithfulness score and details
    """

    def __init__(self):
        """Initialize faithfulness agent."""
        self._claim_extractor = ClaimExtractor()
        self._entailment_checker = EntailmentChecker()
        logger.info("FaithfulnessAgent initialized")

    async def verify(
        self,
        summary: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Verify claims in summary against source documents.
        
        Args:
            summary: Generated narrative summary
            documents: Source documents used for generation
            
        Returns:
            Verification report:
            - total_claims: Number of claims extracted
            - verified_claims: Number of verified claims
            - unverified_claims: Number of unverified claims
            - faithfulness_score: verified_claims / total_claims
            - claim_details: List of detailed claim verification results
        """
        logger.info(
            "[FaithfulnessAgent] Starting verification",
            extra={"summary_len": len(summary), "doc_count": len(documents)},
        )

        # Phase 1: Extract claims
        claims = await self._claim_extractor.extract_claims(summary)
        
        if not claims:
            logger.warning("[FaithfulnessAgent] No claims extracted")
            return {
                "total_claims": 0,
                "verified_claims": 0,
                "unverified_claims": 0,
                "faithfulness_score": 0.0,
                "claim_details": [],
            }

        logger.info(f"[FaithfulnessAgent] Extracted {len(claims)} claims")

        # Phase 2: Verify claims
        verification_results = await self._entailment_checker.check_batch(
            claims,
            documents,
        )

        # Phase 3: Aggregate results
        verified_count = sum(
            1 for r in verification_results
            if r.get("status") == "verified"
        )
        unverified_count = len(verification_results) - verified_count
        
        faithfulness_score = (
            verified_count / len(verification_results)
            if verification_results else 0.0
        )

        # Build detailed report
        claim_details = []
        for result in verification_results:
            claim_details.append({
                "claim": result.get("claim", ""),
                "category": result.get("category", "General"),
                "entailment_score": result.get("entailment_score", 0.0),
                "status": result.get("status", "unverified"),
                "supporting_sources": result.get("supporting_sources", []),
            })

        report = {
            "total_claims": len(claims),
            "verified_claims": verified_count,
            "unverified_claims": unverified_count,
            "faithfulness_score": round(faithfulness_score, 3),
            "claim_details": claim_details,
        }

        logger.info(
            f"[FaithfulnessAgent] Verification complete: "
            f"{verified_count}/{len(claims)} verified ({faithfulness_score:.2f})",
        )

        return report
