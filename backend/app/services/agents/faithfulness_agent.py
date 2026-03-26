"""Faithfulness Agent for claim verification.

Combines claim extraction, entailment checking, citation verification,
and numerical hallucination detection for comprehensive faithfulness assessment.
"""
from __future__ import annotations

import logging
from typing import Any

from ..verification.claim_extractor import ClaimExtractor
from ..verification.entailment_checker import EntailmentChecker
from ..verification.citation_verifier import CitationVerifier
from ..verification.numerical_verifier import NumericalVerifier, get_numerical_verifier

logger = logging.getLogger(__name__)


class FaithfulnessAgent:
    """Verifies claim faithfulness in generated summaries.

    Uses 5-Phase Verification Pipeline (Best Practice):
    1. Extract claims from summary (ClaimExtractor)
    2. Verify claims via NLI entailment (EntailmentChecker)
    3. Verify citations match sources (CitationVerifier)
    4. Verify numerical claims (NumericalVerifier) - NEW
    5. Detect hallucinations vs misattribution (separate failure modes)
    """

    def __init__(self):
        """Initialize faithfulness agent."""
        self._claim_extractor = ClaimExtractor()
        self._entailment_checker = EntailmentChecker()
        self._citation_verifier = CitationVerifier()
        self._numerical_verifier = get_numerical_verifier(tolerance=0.10)
        logger.info("FaithfulnessAgent initialized with best-practice verification")

    async def verify(
        self,
        summary: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Verify claims and citations in summary against source documents.

        Args:
            summary: Generated narrative summary with citations
            documents: Source documents used for generation

        Returns:
            Comprehensive verification report:
            - total_claims: Number of claims extracted
            - verified_claims: Number of NLI-verified claims
            - faithfulness_score: verified_claims / total_claims
            - hallucination_analysis: TRUE hallucinations (fabricated claims)
            - misattribution_analysis: Claims with wrong citations
            - numerical_hallucinations: Fabricated numbers
            - citation_verification: Citation accuracy report
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
                "hallucination_analysis": None,
                "misattribution_analysis": None,
                "numerical_hallucinations": None,
                "citation_verification": None,
            }

        logger.info(f"[FaithfulnessAgent] Extracted {len(claims)} claims")

        # Phase 2: Verify claims via NLI (any document)
        verification_results = await self._entailment_checker.check_batch(
            claims,
            documents,
        )

        # Phase 3: Verify citations (metadata accuracy)
        citation_report = self._citation_verifier.verify_all_citations(
            summary=summary,
            documents=documents,
        )

        logger.info(
            f"[FaithfulnessAgent] Citation verification: "
            f"{citation_report['valid_citations']}/{citation_report['total_citations']} "
            f"({citation_report['citation_accuracy_rate']:.2f})",
        )

        # Phase 4: Verify numerical claims (NEW - best practice)
        numerical_results = self._numerical_verifier.verify_batch(
            claims=claims,
            documents=documents,
        )

        # Phase 5: Aggregate with proper separation
        # CRITICAL: Separate hallucination from misattribution
        analysis = self._analyze_with_separation(
            verification_results=verification_results,
            citation_report=citation_report,
            numerical_results=numerical_results,
            claims=claims,
            summary=summary,  # Pass summary for claim extraction
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

        verified_count = sum(
            1 for r in verification_results
            if r.get("status") == "verified"
        )
        faithfulness_score = (
            verified_count / len(verification_results)
            if verification_results else 0.0
        )

        report = {
            "total_claims": len(claims),
            "verified_claims": verified_count,
            "unverified_claims": len(verification_results) - verified_count,
            "faithfulness_score": round(faithfulness_score, 3),
            "claim_details": claim_details,
            "hallucination_analysis": analysis["hallucination_analysis"],
            "misattribution_analysis": analysis["misattribution_analysis"],
            "numerical_hallucinations": analysis["numerical_hallucinations"],
            "citation_verification": citation_report,
        }

        logger.info(
            f"[FaithfulnessAgent] Verification complete: "
            f"{verified_count}/{len(claims)} verified ({faithfulness_score:.2f}), "
            f"{analysis['hallucination_analysis']['hallucination_count']} hallucinations, "
            f"{analysis['misattribution_analysis']['misattribution_count']} misattributions",
        )

        return report

    def _analyze_with_separation(
        self,
        verification_results: list[dict[str, Any]],
        citation_report: dict[str, Any],
        numerical_results: list[dict[str, Any]],
        claims: list[dict[str, Any]],
        summary: str,
    ) -> dict[str, Any]:
        """Analyze with proper separation of failure modes.

        BEST PRACTICE: Separate these distinct failure modes:
        1. Hallucination: Claim is fabricated (not supported by ANY document)
        2. Misattribution: Claim is true but cited to WRONG source
        3. Numerical Hallucination: Numbers fabricated or unsupported
        4. Unsupported: Claim not entailed (low score, but not contradiction)
        """
        # ─────────────────────────────────────────────────────────────
        # 1. TRUE HALLUCINATIONS: Claims not supported by ANY document
        # ─────────────────────────────────────────────────────────────
        hallucination_details = []
        hallucination_types = {
            "fabricated_claim": 0,  # Not in any source
            "contradicted_claim": 0,  # Contradicts sources
            "numerical_hallucination": 0,  # Numbers unsupported
        }

        for result in verification_results:
            claim_text = result.get("claim", "")
            entailment_score = result.get("entailment_score", 0.0)
            status = result.get("status", "unverified")

            # TRUE hallucination: claim NOT entailed by any document
            if status == "contradicted":
                hallucination_details.append({
                    "type": "contradicted_claim",
                    "claim": claim_text,
                    "category": result.get("category", "General"),
                    "entailment_score": entailment_score,
                    "reason": "Claim contradicts source documents",
                })
                hallucination_types["contradicted_claim"] += 1

            elif status == "unverified" and entailment_score < 0.50:
                # Low entailment = likely fabricated
                hallucination_details.append({
                    "type": "fabricated_claim",
                    "claim": claim_text,
                    "category": result.get("category", "General"),
                    "entailment_score": entailment_score,
                    "reason": "Claim not supported by any source document",
                })
                hallucination_types["fabricated_claim"] += 1

        # ─────────────────────────────────────────────────────────────
        # 2. NUMERICAL HALLUCINATIONS: Fabricated numbers
        # ─────────────────────────────────────────────────────────────
        numerical_hallucination_details = []
        for num_result in numerical_results:
            if not num_result.get("verified", True):
                # Find corresponding claim
                claim_text = num_result.get("claim", "")
                for h_detail in hallucination_details:
                    if h_detail["claim"] == claim_text:
                        # Already counted as fabricated
                        break
                else:
                    # New: numerical hallucination only
                    numerical_hallucination_details.append({
                        "claim": claim_text,
                        "category": num_result.get("category", "General"),
                        "unsupported_numbers": num_result.get("mismatches", []),
                        "reason": f"Numbers not found in sources: {num_result.get('mismatches')}",
                    })
                    hallucination_types["numerical_hallucination"] += 1

        # ─────────────────────────────────────────────────────────────
        # 3. MISATTRIBUTION: Claim true, but citation WRONG
        # ─────────────────────────────────────────────────────────────
        misattribution_details = []

        for citation_detail in citation_report.get("citation_details", []):
            if not citation_detail.get("is_valid", True):
                # Extract claim associated with this citation
                claim_text, _, _ = self._citation_verifier.extract_claim_with_citation(
                    summary,  # Fixed: use summary parameter, not citation_report.get("summary")
                    citation_detail.get("position", 0),
                )

                # Check if this claim is actually verified by SOME document
                is_verified_by_any = any(
                    r.get("claim") == claim_text and r.get("status") == "verified"
                    for r in verification_results
                )

                if is_verified_by_any:
                    # Claim is true, but citation is wrong = MISATTRIBUTION
                    misattribution_details.append({
                        "type": "misattribution",
                        "claim": claim_text,
                        "citation": citation_detail.get("citation"),
                        "accuracy_score": citation_detail.get("accuracy_score", 0.0),
                        "reason": citation_detail.get("error", "Citation metadata inaccurate"),
                    })
                # Else: already counted as hallucination above

        # ─────────────────────────────────────────────────────────────
        # 4. AGGREGATE METRICS
        # ─────────────────────────────────────────────────────────────
        total_claims = len(verification_results)
        hallucination_count = len(hallucination_details)
        misattribution_count = len(misattribution_details)
        numerical_hallucination_count = len(numerical_hallucination_details)

        return {
            "hallucination_analysis": {
                "hallucination_count": hallucination_count,
                "hallucination_details": hallucination_details,
                "hallucination_rate": round(hallucination_count / total_claims, 3) if total_claims > 0 else 0.0,
                "hallucination_types": hallucination_types,
                "is_hallucination_free": hallucination_count == 0,
            },
            "misattribution_analysis": {
                "misattribution_count": misattribution_count,
                "misattribution_details": misattribution_details,
                "misattribution_rate": round(misattribution_count / total_claims, 3) if total_claims > 0 else 0.0,
            },
            "numerical_hallucinations": {
                "count": numerical_hallucination_count,
                "details": numerical_hallucination_details,
                "rate": round(numerical_hallucination_count / total_claims, 3) if total_claims > 0 else 0.0,
            },
        }
