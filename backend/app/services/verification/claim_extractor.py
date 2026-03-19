"""Claim extraction module for faithfulness verification.

Extracts individual factual claims from generated summaries for verification.
"""
from __future__ import annotations

import logging
from typing import Any

from ..llm.groq_provider import get_groq_provider

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extracts factual claims from text using LLM.
    
    Uses Groq llama-4-scout for fast, accurate claim extraction.
    """

    def __init__(self, model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        """Initialize claim extractor.
        
        Args:
            model_name: Groq model to use for extraction
        """
        from ...core.config import get_settings
        settings = get_settings()
        
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY not configured")
        
        self._model = get_groq_provider(model_name)
        logger.info(f"[ClaimExtractor] Initialized with Groq: {model_name}")

    async def extract_claims(self, summary: str) -> list[dict[str, Any]]:
        """Extract individual factual claims from summary.
        
        Args:
            summary: Generated narrative summary text
            
        Returns:
            List of claim dictionaries with:
            - claim: The factual claim text
            - category: Theme/category (Infrastructure, Health, Safety, etc.)
        """
        if not summary or len(summary.strip()) < 10:
            logger.warning("[ClaimExtractor] Summary too short for claim extraction")
            return []

        prompt = self._build_extraction_prompt(summary)
        
        try:
            import time
            start = time.perf_counter()
            
            raw_text = await self._model.generate(
                prompt=prompt,
                system_prompt="You are a claim extraction specialist. Return ONLY valid JSON array of claims (no markdown, no code blocks).",
                temperature=0.1,
                max_tokens=4000,
            )
            
            elapsed = time.perf_counter() - start
            logger.info(f"[ClaimExtractor] Extracted claims in {elapsed:.2f}s")
            
            # Parse JSON response
            claims = self._parse_claims(raw_text)
            return claims
            
        except Exception as exc:
            logger.exception(f"[ClaimExtractor] Claim extraction failed: {exc}")
            return []

    def _build_extraction_prompt(self, summary: str) -> str:
        """Build prompt for claim extraction."""
        return (
            "Extract ALL factual claims from the following Baguio City civic summary.\n\n"
            "A FACTUAL CLAIM is:\n"
            "- A specific, verifiable statement about events, conditions, or situations\n"
            "- NOT opinions, generalizations, or vague statements\n"
            "- NOT citations like [Src: facebook.com | Cred: 0.87 | Sent: Negative]\n\n"
            "Examples:\n"
            "✓ 'Traffic increased on Session Road' ← Factual claim\n"
            "✓ 'Water shortage concerns persist' ← Factual claim\n"
            "✗ 'The situation is concerning' ← Opinion (skip)\n"
            "✗ 'Residents are worried' ← Vague (skip)\n\n"
            "SUMMARY TO ANALYZE:\n"
            f"{summary}\n\n"
            "Return a JSON array of claims. Each claim must have:\n"
            "- claim: The factual claim text (exact wording from summary)\n"
            "- category: Theme category (Infrastructure/Health/Safety/Tourism/Economy/Environment/General)\n\n"
            "Example output:\n"
            '[{"claim": "Traffic increased on Session Road", "category": "Infrastructure"}, {"claim": "Water shortage concerns persist", "category": "Infrastructure"}]\n\n'
            "Return ONLY the JSON array (no markdown, no code blocks, no explanations)."
        )

    def _parse_claims(self, raw_text: str) -> list[dict[str, Any]]:
        """Parse LLM response into claim list."""
        import json
        import re
        
        if not raw_text:
            return []
        
        text = raw_text.strip()
        
        # Try to extract JSON array from response
        json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        try:
            claims = json.loads(text)
            if not isinstance(claims, list):
                logger.warning(f"[ClaimExtractor] Expected list, got {type(claims)}")
                return []
            
            # Validate claim structure
            valid_claims = []
            for claim in claims:
                if isinstance(claim, dict) and "claim" in claim:
                    # Clean claim text (remove citations)
                    claim_text = claim["claim"]
                    claim_text = re.sub(r'\s*\[Src:.*?\]', '', claim_text).strip()
                    
                    if len(claim_text) > 5:  # Minimum claim length
                        valid_claims.append({
                            "claim": claim_text,
                            "category": claim.get("category", "General"),
                        })
            
            logger.info(f"[ClaimExtractor] Validated {len(valid_claims)}/{len(claims)} claims")
            return valid_claims
            
        except json.JSONDecodeError as exc:
            logger.warning(f"[ClaimExtractor] JSON parse failed: {exc}")
            logger.debug(f"[ClaimExtractor] Raw text: {raw_text[:500]}")
            return []
