"""Claim extraction module for faithfulness verification.

Extracts individual factual claims from generated summaries for verification.
"""
from __future__ import annotations

import logging
from typing import Any

from ..llm.factory import get_llm_for_mode

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extracts factual claims from text using LLM.

    The provider is resolved per request from the requested mode:
    ``cloud`` uses Groq ``groq/compound``, ``local`` uses Ollama Qwen.
    Extraction is retried up to five times on transient LLM failures.
    """

    def __init__(self, model_name: str | None = None):
        """Initialize claim extractor.

        Args:
            model_name: Optional model override passed to the provider factory.
        """
        self._model_name = model_name
        logger.info("[ClaimExtractor] provider resolved per request")

    def _resolve_model(self, llm_mode: str | None = None):
        """Resolve the LLM provider for this request's mode."""
        return get_llm_for_mode(llm_mode, model=self._model_name)

    async def extract_claims(self, summary: str, llm_mode: str | None = None) -> list[dict[str, Any]]:
        """Extract individual factual claims from summary.
        
        Args:
            summary: Generated narrative summary text
            llm_mode: Requested LLM mode ("cloud" or "local"); None uses the active mode
            
        Returns:
            List of claim dictionaries with:
            - claim: The factual claim text
            - category: Theme/category (Infrastructure, Health, Safety, etc.)
        """
        if not summary or len(summary.strip()) < 10:
            logger.warning("[ClaimExtractor] Summary too short for claim extraction")
            return []

        prompt = self._build_extraction_prompt(summary)

        import time
        import asyncio

        for attempt in range(1, 6):
            try:
                start = time.perf_counter()

                raw_text = await self._resolve_model(llm_mode).generate(
                    prompt=prompt,
                    system_prompt="You are a claim extraction specialist. Return ONLY valid JSON array of claims (no markdown, no code blocks).",
                    temperature=0.1,
                    max_tokens=4000,
                )

                elapsed = time.perf_counter() - start
                logger.info(f"[ClaimExtractor] Extracted claims in {elapsed:.2f}s")

                claims = self._parse_claims(raw_text)
                return claims

            except Exception as exc:
                if attempt == 5:
                    logger.exception(f"[ClaimExtractor] Claim extraction failed after {attempt} attempts: {exc}")
                    return []
                delay = 2.0 * (2 ** (attempt - 1))
                logger.warning(f"[ClaimExtractor] Attempt {attempt} failed ({exc}), retrying in {delay:.1f}s")
                await asyncio.sleep(delay)

        return []  # Unreachable: loop returns on success or final attempt.

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
