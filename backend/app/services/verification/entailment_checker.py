"""Entailment checking module for claim verification.

Uses NLI (Natural Language Inference) to check if claims are supported by source documents.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class EntailmentChecker:
    """Checks if claims are entailed by source documents using NLI.

    Uses DeBERTa-v3 NLI model for entailment checking:
    - Entailment: Claim is supported by document
    - Neutral: Claim is unrelated to document
    - Contradiction: Claim contradicts document
    
    GPU Support: Automatically detects and uses CUDA/MPS if available.
    Falls back to CPU if no GPU is found or NLI_USE_GPU=false env var is set.
    """

    MODEL_NAME = "MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33"
    ENTAILMENT_THRESHOLD = 0.70  # Minimum score for "verified"

    def __init__(self, use_gpu: bool = None):
        """Initialize entailment checker with NLI model.
        
        Args:
            use_gpu: Force GPU usage (True), force CPU (False), or auto-detect (None).
                    Can also be set via NLI_USE_GPU environment variable.
        """
        self._model = None
        self._tokenizer = None
        self._device = None
        self._use_gpu = use_gpu
        logger.info(f"[EntailmentChecker] Initializing (model: {self.MODEL_NAME})")

    def _load_model(self):
        """Lazy-load NLI model with GPU support."""
        if self._model is not None:
            return

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch

            # Determine device preference
            use_gpu = self._use_gpu
            if use_gpu is None:
                # Auto-detect from environment variable
                use_gpu = os.getenv("NLI_USE_GPU", "true").lower() == "true"

            # Select best available device
            if use_gpu and torch.cuda.is_available():
                self._device = torch.device("cuda")
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"[EntailmentChecker] CUDA available: {gpu_name}")
            elif use_gpu and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # Apple Silicon MPS
                self._device = torch.device("mps")
                logger.info("[EntailmentChecker] Apple Silicon MPS available")
            else:
                self._device = torch.device("cpu")
                if use_gpu:
                    logger.warning("[EntailmentChecker] GPU requested but not available, falling back to CPU")

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)

            # Load model
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                torch_dtype=torch.float32,
            )

            # Set to evaluation mode
            self._model.eval()

            # Move to selected device
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

        # Check entailment for all snippets in parallel (batch processing)
        scores = []
        supporting = []

        try:
            import torch

            with torch.no_grad():
                # Batch tokenize all snippets at once (parallel GPU processing)
                # NLI format: premise (document) → hypothesis (claim)
                inputs = self._tokenizer(
                    snippets,
                    [claim] * len(snippets),  # Repeat claim for each snippet
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True,  # Pad to longest sequence in batch
                )

                # Move entire batch to device
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                # Single forward pass for all documents (parallel on GPU)
                outputs = self._model(**inputs)
                logits = outputs.logits

                # Convert to probabilities (batch dimension preserved)
                probs = torch.softmax(logits, dim=-1)

                # Extract entailment scores for all snippets
                for i, url in enumerate(urls):
                    # DeBERTa-v3-base-zeroshot-v1.1-all-33 returns 2 labels: [not_entailment, entailment]
                    # Some DeBERTa models return 3 labels: [contradiction, neutral, entailment]
                    # Handle both cases dynamically
                    if len(probs[i]) == 2:
                        # 2-label model: [not_entailment, entailment]
                        entailment_score = probs[i][1].item()
                        contradiction_score = probs[i][0].item()
                    else:
                        # 3-label model: [contradiction, neutral, entailment]
                        entailment_score = probs[i][2].item()
                        contradiction_score = probs[i][0].item()

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

    def preload_model(self):
        """Preload and cache model (call on startup).
        
        Follows same pattern as RoBERTa and BGE embedding models
        for consistency across codebase.
        """
        logger.info("[EntailmentChecker] Preloading model...")
        self._load_model()
        logger.info("[EntailmentChecker] Model preloaded and cached")


# Module-level singleton instance (follows sentiment_agent.py pattern)
_entailment_checker_instance: EntailmentChecker | None = None


def get_entailment_checker(use_gpu: bool = None) -> EntailmentChecker:
    """Get or create singleton EntailmentChecker instance.
    
    Follows same pattern as get_sentiment_model() and get_embedding_service()
    for consistency across codebase.
    
    Args:
        use_gpu: Force GPU usage (True), force CPU (False), or auto-detect (None)
    
    Returns:
        Singleton EntailmentChecker instance
    """
    global _entailment_checker_instance
    
    if _entailment_checker_instance is None:
        logger.info("[EntailmentChecker] Creating singleton instance")
        _entailment_checker_instance = EntailmentChecker(use_gpu=use_gpu)
        # Preload model on first access (lazy loading)
        _entailment_checker_instance.preload_model()
    
    return _entailment_checker_instance
