"""Entailment checking module for claim verification.

Uses NLI (Natural Language Inference) to check if claims are supported by source documents.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class EntailmentChecker:
    """Checks if claims are entailed by source documents using NLI.
    
    Uses DeBERTa-v3 NLI model for entailment checking:
    - Entailment: Claim is supported by document
    - Neutral: Claim is unrelated to document
    - Contradiction: Claim contradicts document
    """

    MODEL_NAME = "MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33"
    ENTAILMENT_THRESHOLD = 0.70  # Minimum score for "verified"

    def __init__(self):
        """Initialize entailment checker with NLI model."""
        self._model = None
        self._tokenizer = None
        self._device = None
        logger.info(f"[EntailmentChecker] Initializing (model: {self.MODEL_NAME})")

    def _load_model(self):
        """Lazy-load NLI model."""
        if self._model is not None:
            return
        
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            
            # Load model
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                torch_dtype=torch.float32,
            )
            
            # Set to evaluation mode
            self._model.eval()
            
            # Use CPU (optimized for 16GB RAM environment)
            self._device = torch.device("cpu")
            self._model.to(self._device)
            
            logger.info(f"[EntailmentChecker] Model loaded on {self._device}")
            
        except Exception as exc:
            logger.exception(f"[EntailmentChecker] Failed to load model: {exc}")
            raise

    async def check_entailment(
        self,
        claim: str,
        documents: list[dict[str, Any]],
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Check if claim is entailed by any of the documents.
        
        Args:
            claim: Factual claim to verify
            documents: List of source documents (with 'snippet' or 'content')
            top_k: Number of top documents to check (by relevance)
            
        Returns:
            Verification result:
            - entailment_score: Max score across all documents (0.0-1.0)
            - status: "verified" | "unverified" | "contradicted"
            - supporting_sources: List of URLs that support the claim
        """
        if not claim or not documents:
            return {
                "entailment_score": 0.0,
                "status": "unverified",
                "supporting_sources": [],
            }

        # Lazy-load model
        self._load_model()

        # Get top-k document snippets
        snippets = []
        urls = []
        for doc in documents[:top_k]:
            snippet = doc.get("snippet", "") or doc.get("content", "")
            url = doc.get("url")
            if snippet and len(snippet) > 10:
                snippets.append(snippet[:500])  # Truncate for efficiency
                urls.append(url)

        if not snippets:
            return {
                "entailment_score": 0.0,
                "status": "unverified",
                "supporting_sources": [],
            }

        # Check entailment for each snippet
        scores = []
        supporting = []
        
        try:
            import torch
            
            with torch.no_grad():
                for i, (snippet, url) in enumerate(zip(snippets, urls)):
                    # NLI format: premise (document) → hypothesis (claim)
                    inputs = self._tokenizer(
                        snippet,
                        claim,
                        return_tensors="pt",
                        truncation=True,
                        max_length=512,
                        padding=True,
                    )
                    
                    # Move to device
                    inputs = {k: v.to(self._device) for k, v in inputs.items()}

                    # Get model output
                    outputs = self._model(**inputs)
                    logits = outputs.logits

                    # Convert to probabilities
                    probs = torch.softmax(logits, dim=-1)[0]

                    # DeBERTa-v3-base-zeroshot-v1.1-all-33 returns 2 labels: [not_entailment, entailment]
                    # Some DeBERTa models return 3 labels: [contradiction, neutral, entailment]
                    # Handle both cases dynamically
                    if len(probs) == 2:
                        # 2-label model: [not_entailment, entailment]
                        entailment_score = probs[1].item()
                        contradiction_score = probs[0].item()
                    else:
                        # 3-label model: [contradiction, neutral, entailment]
                        entailment_score = probs[2].item()
                        contradiction_score = probs[0].item()

                    scores.append(entailment_score)

                    # Consider as supporting if entailment > threshold
                    if entailment_score >= self.ENTAILMENT_THRESHOLD:
                        supporting.append(url)
            
            max_score = max(scores) if scores else 0.0
            
            # Determine status
            if max_score >= self.ENTAILMENT_THRESHOLD:
                status = "verified"
            elif max_score < 0.3:  # Low score = likely contradiction
                status = "contradicted"
            else:
                status = "unverified"
            
            logger.info(
                f"[EntailmentChecker] Claim verified: {status} (score={max_score:.3f})",
                extra={"claim": claim[:50], "supporting_count": len(supporting)},
            )
            
            return {
                "entailment_score": round(max_score, 3),
                "status": status,
                "supporting_sources": [url for url in supporting if url],
            }
            
        except Exception as exc:
            logger.exception(f"[EntailmentChecker] Entailment check failed: {exc}")
            return {
                "entailment_score": 0.5,  # Neutral on error
                "status": "unverified",
                "supporting_sources": [],
            }

    async def check_batch(
        self,
        claims: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Check entailment for multiple claims.
        
        Args:
            claims: List of claim dictionaries with 'claim' key
            documents: Source documents
            
        Returns:
            List of verification results (one per claim)
        """
        results = []
        
        for claim_dict in claims:
            claim_text = claim_dict.get("claim", "")
            result = await self.check_entailment(claim_text, documents)
            result["claim"] = claim_text
            result["category"] = claim_dict.get("category", "General")
            results.append(result)
        
        return results
