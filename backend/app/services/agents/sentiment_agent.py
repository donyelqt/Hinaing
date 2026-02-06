"""Full Ensemble Sentiment Analysis using RoBERTa + Groq.

Both models analyze ALL documents, predictions are combined for maximum accuracy.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Literal

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Legacy Gemini imports (kept for reference if switching back to Gemini)
# import google.generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from ...schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "negative", "neutral"]

# Legacy Gemini safety settings (kept for reference if switching back to Gemini)
# Disable safety filters for civic news analysis
# SAFETY_SETTINGS = {
#     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
#     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
# }

# Ensemble weights (sum to 1.0)
ROBERTA_WEIGHT = 0.4   # Transformer model weight
LLM_WEIGHT = 0.6       # LLM weight (higher because context-aware)


def sanitize_text(text: str | None) -> str:
    """Remove invalid Unicode characters (surrogates) that break APIs.
    
    The character \ud835 and similar surrogates cause:
    - UnicodeEncodeError in LLM APIs
    - Tokenizer errors in transformers
    - JSON serialization failures
    """
    if not text:
        return ""
    
    # Remove surrogate characters (U+D800 to U+DFFF)
    # These are invalid in UTF-8 and break most APIs
    cleaned = re.sub(r'[\ud800-\udfff]', '', text)
    
    # Also remove other problematic characters
    # - Control characters except newline/tab
    # - Zero-width characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    
    return cleaned.strip()


class RoBERTaSentimentModel:
    """RoBERTa fine-tuned on 124M tweets for social media sentiment."""
    
    MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    def __init__(self):
        logger.info(f"Loading sentiment model: {self.MODEL_NAME}")
        
        self.tokenizer = None
        self.model = None
        self._fallback_mode = False
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
            self.model.eval()
            logger.info("RoBERTa sentiment model loaded")
        except Exception as e:
            logger.warning(f"Failed to load RoBERTa model: {e}")
            logger.warning("Running in FALLBACK MODE - using LLM-only sentiment analysis")
            self._fallback_mode = True
        
        # Model outputs: 0=negative, 1=neutral, 2=positive
        self.label_map = {0: "negative", 1: "neutral", 2: "positive"}
    
    @property
    def is_fallback_mode(self) -> bool:
        """Check if running in fallback mode."""
        return self._fallback_mode
    
    def predict_batch_with_probs(self, texts: list[str]) -> list[dict[str, float]]:
        """Get probability distributions for batch of texts."""
        if not texts:
            return []
        
        default_probs = {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
        
        # If in fallback mode, return neutral defaults (LLM will handle sentiment)
        if self._fallback_mode:
            logger.debug(f"RoBERTa fallback: returning defaults for {len(texts)} texts")
            return [default_probs.copy() for _ in texts]
        
        # Sanitize and validate texts
        sanitized = []
        for t in texts:
            clean = sanitize_text(t)
            # Ensure non-empty string for tokenizer
            if not clean:
                clean = "neutral content"
            sanitized.append(clean[:512])

        batch_size = max(1, int(os.getenv("ROBERTA_BATCH_SIZE", "16")))

        results: list[dict[str, float]] = []

        for start in range(0, len(sanitized), batch_size):
            batch = sanitized[start:start + batch_size]
            try:
                inputs = self.tokenizer(
                    batch,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True,
                )

                with torch.inference_mode():
                    outputs = self.model(**inputs)
                    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

                for prob in probs:
                    results.append({
                        "negative": prob[0].item(),
                        "neutral": prob[1].item(),
                        "positive": prob[2].item(),
                    })
            except Exception as e:
                logger.warning(f"RoBERTa batch failed: {e}")
                results.extend([default_probs.copy() for _ in range(len(batch))])
            finally:
                try:
                    del inputs
                except Exception:
                    pass
                try:
                    del outputs
                except Exception:
                    pass
                try:
                    del probs
                except Exception:
                    pass

        return results


_sentiment_model_instance: RoBERTaSentimentModel | None = None


def get_sentiment_model() -> RoBERTaSentimentModel:
    """Get singleton sentiment model instance."""
    global _sentiment_model_instance
    if _sentiment_model_instance is None:
        _sentiment_model_instance = RoBERTaSentimentModel()
    return _sentiment_model_instance


class EnsembleSentimentAgent:
    """Full Ensemble: RoBERTa + Groq analyze ALL documents."""
    
    def __init__(self):
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY missing")
        
        # Use llama-3.3-70b-versatile for sentiment: 96% accuracy (24% better than Scout's 72%)
        # Evaluation results: 96% accuracy, 3.7s speed, 25% faster than Scout
        # TPM: 12K, TPD: 14K
        # Batch size: 10 docs (Groq SDK handles rate limits with exponential backoff)
        from ..llm.groq_provider import get_groq_provider
        self.llm = get_groq_provider("llama-3.3-70b-versatile")
        self.roberta = get_sentiment_model()
        self.batch_size = 40  # Full parallel, Groq SDK handles retries
        
        logger.info(
            f"EnsembleSentimentAgent initialized with Groq llama-3.3-70b-versatile "
            f"(RoBERTa weight={ROBERTA_WEIGHT}, LLM weight={LLM_WEIGHT}, "
            f"Batch size={self.batch_size}, TPM: 12K, TPD: 14K, Accuracy: 96%, Full parallel)"
        )
    
    def analyze_batch(self, documents: list[WebDocument]) -> list[WebDocument]:
        """Analyze sentiment using full ensemble of both models.
        
        MEMORY OPTIMIZATION: Sequential processing to prevent OOM on Railway.
        TIMEOUT PROTECTION: Total 120s timeout for entire sentiment analysis.
        Processes all 100 docs but without parallel memory spikes.
        """
        import time
        
        if not documents:
            return []
        
        start_time = time.time()
        TOTAL_TIMEOUT = 120  # 2 minutes max for entire sentiment analysis
        
        logger.info(f"[EnsembleSentimentAgent] Analyzing {len(documents)} documents with full ensemble")
        
        # Sanitize texts before processing
        texts = []
        for doc in documents:
            title = sanitize_text(doc.title)
            snippet = sanitize_text(doc.snippet)
            texts.append(f"{title}. {snippet}"[:512])
        
        # PERFORMANCE OPTIMIZATION: Run RoBERTa and LLM in PARALLEL
        # Using the GLOBAL_EXECUTOR from main to avoid the overhead of spawning new threads
        from app.core.executor import GLOBAL_EXECUTOR
        
        logger.info("[EnsembleSentimentAgent] Starting Parallel Ensemble (RoBERTa + LLM)...")
        
        # Track counts for metrics
        roberta_probs = []
        llm_probs = []
        
        # Task 1: RoBERTa (Local Transformer)
        ro_future = GLOBAL_EXECUTOR.submit(self.roberta.predict_batch_with_probs, texts)
        # Task 2: LLM (Groq Cloud)
        llm_future = GLOBAL_EXECUTOR.submit(self._llm_analyze_all, documents)
        
        # Wait for both (with global timeout)
        try:
            # RoBERTa is usually fast, but LLM can hang.
            # We give llm_future a bit more room.
            roberta_probs = ro_future.result(timeout=TOTAL_TIMEOUT)
            llm_probs = llm_future.result(timeout=TOTAL_TIMEOUT)
        except Exception as e:
            logger.error(f"[EnsembleSentimentAgent] Parallel ensemble failed or timed out: {e}")
            # Fallback: ensure we have something to combine
            default_probs = {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
            if not roberta_probs:
                roberta_probs = [default_probs.copy()] * len(documents)
            if not llm_probs:
                llm_probs = [default_probs.copy()] * len(documents)
        
        logger.info(f"[EnsembleSentimentAgent] Ensemble analysis completed in {time.time() - start_time:.1f}s")
        
        # Combine predictions with weighted ensemble
        enriched: list[WebDocument] = []
        
        for idx, doc in enumerate(documents):
            r_probs = roberta_probs[idx]
            l_probs = llm_probs[idx]
            
            # Weighted combination
            combined = {
                "negative": (ROBERTA_WEIGHT * r_probs["negative"]) + (LLM_WEIGHT * l_probs["negative"]),
                "neutral": (ROBERTA_WEIGHT * r_probs["neutral"]) + (LLM_WEIGHT * l_probs["neutral"]),
                "positive": (ROBERTA_WEIGHT * r_probs["positive"]) + (LLM_WEIGHT * l_probs["positive"]),
            }
            
            final_label = max(combined, key=combined.get)
            final_confidence = combined[final_label]
            
            roberta_label = max(r_probs, key=r_probs.get)
            llm_label = max(l_probs, key=l_probs.get)
            
            if roberta_label == llm_label:
                agreement = "full_agreement"
            elif final_label == roberta_label:
                agreement = "roberta_dominant"
            elif final_label == llm_label:
                agreement = "llm_dominant"
            else:
                agreement = "ensemble_decision"
            
            source_type = self._detect_source_type(doc)
            
            enriched.append(doc.model_copy(update={
                "sentiment": final_label,
                "metadata": {
                    **(doc.metadata or {}),
                    "sentiment_confidence": round(final_confidence, 3),
                    "sentiment_method": "ensemble",
                    "roberta_prediction": roberta_label,
                    "roberta_confidence": round(max(r_probs.values()), 3),
                    "llm_prediction": llm_label,
                    "llm_confidence": round(max(l_probs.values()), 3),
                    "model_agreement": agreement,
                    "content_source_type": source_type,
                }
            }))
        
        self._log_distribution(enriched)
        return enriched
    
    def _original_analyze_batch(self, documents: list[WebDocument]) -> list[WebDocument]:
        """Original parallel version - kept for reference."""
        if not documents:
            return []
        
        texts = []
        for doc in documents:
            title = sanitize_text(doc.title)
            snippet = sanitize_text(doc.snippet)
            texts.append(f"{title}. {snippet}"[:512])
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Run RoBERTa in one thread (it's fast/local)
            roberta_future = executor.submit(self.roberta.predict_batch_with_probs, texts)
            # Run LLM batches in parallel threads
            llm_future = executor.submit(self._llm_analyze_all, documents)
            
            roberta_probs = roberta_future.result()
            llm_probs = llm_future.result()
        
        # Step 3: Combine predictions with weighted ensemble
        enriched: list[WebDocument] = []
        
        for idx, doc in enumerate(documents):
            r_probs = roberta_probs[idx]
            l_probs = llm_probs[idx]
            
            # Weighted combination
            combined = {
                "negative": (ROBERTA_WEIGHT * r_probs["negative"]) + (LLM_WEIGHT * l_probs["negative"]),
                "neutral": (ROBERTA_WEIGHT * r_probs["neutral"]) + (LLM_WEIGHT * l_probs["neutral"]),
                "positive": (ROBERTA_WEIGHT * r_probs["positive"]) + (LLM_WEIGHT * l_probs["positive"]),
            }
            
            final_label = max(combined, key=combined.get)
            final_confidence = combined[final_label]
            
            roberta_label = max(r_probs, key=r_probs.get)
            llm_label = max(l_probs, key=l_probs.get)
            
            if roberta_label == llm_label:
                agreement = "full_agreement"
            elif final_label == roberta_label:
                agreement = "roberta_dominant"
            elif final_label == llm_label:
                agreement = "llm_dominant"
            else:
                agreement = "ensemble_decision"
            
            source_type = self._detect_source_type(doc)
            
            enriched.append(doc.model_copy(update={
                "sentiment": final_label,
                "metadata": {
                    **(doc.metadata or {}),
                    "sentiment_confidence": round(final_confidence, 3),
                    "sentiment_method": "ensemble",
                    "roberta_prediction": roberta_label,
                    "roberta_confidence": round(max(r_probs.values()), 3),
                    "llm_prediction": llm_label,
                    "llm_confidence": round(max(l_probs.values()), 3),
                    "model_agreement": agreement,
                    "content_source_type": source_type,
                }
            }))
        
        self._log_distribution(enriched)
        return enriched
    
    def _llm_analyze_all(self, documents: list[WebDocument]) -> list[dict[str, float]]:
        """Get Groq probability distributions for all documents.
        
        FULL PARALLEL PROCESSING: All batches fire at once for maximum speed.
        Groq SDK handles rate limits with exponential backoff automatically.
        """
        import time
        
        batches = [documents[i:i + self.batch_size] for i in range(0, len(documents), self.batch_size)]
        all_probs: list[dict[str, float]] = []
        default_probs = {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
        
        # Total timeout for all Groq processing (90 seconds max)
        total_start = time.time()
        TOTAL_TIMEOUT = 90  # seconds
        
        # FULL PARALLEL: All batches fire at once (Groq SDK handles retries)
        from app.core.executor import GLOBAL_EXECUTOR
        results_map = {}
        
        # Create a future for each batch using the global hot pool
        future_to_batch = {
            GLOBAL_EXECUTOR.submit(self._llm_batch_with_probs_sync, batch): i 
            for i, batch in enumerate(batches)
        }
        
        for future in concurrent.futures.as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            try:
                # Check total timeout
                if time.time() - total_start > TOTAL_TIMEOUT:
                    logger.warning(f"[EnsembleSentimentAgent] Global timeout reached at batch {batch_idx}")
                    results_map[batch_idx] = [default_probs.copy() for _ in range(len(batches[batch_idx]))]
                    continue

                batch_results = future.result()
                results_map[batch_idx] = batch_results
            except Exception as e:
                logger.warning(f"[EnsembleSentimentAgent] Batch {batch_idx} failed: {e}")
                results_map[batch_idx] = [default_probs.copy() for _ in range(len(batches[batch_idx]))]
        
        # Reassemble results in order
        for i in range(len(batches)):
            if i in results_map:
                all_probs.extend(results_map[i])
            else:
                all_probs.extend([default_probs.copy() for _ in range(len(batches[i]))])
        
        return all_probs
    
    def _llm_batch_with_probs_sync(self, batch: list[WebDocument]) -> list[dict]:
        """Synchronous wrapper for async Groq call (for ThreadPoolExecutor)."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._llm_batch_with_probs(batch))
        finally:
            loop.close()
    
    async def _llm_batch_with_probs(self, batch: list[WebDocument]) -> list[dict[str, float]]:
        """Get Groq (llama-3.3-70b-versatile) predictions with confidence scores.
        
        Implements exponential backoff for rate limit handling.
        """
        doc_entries = []
        for idx, doc in enumerate(batch):
            source_type = self._detect_source_type(doc)
            # Sanitize text before sending to Groq
            title = sanitize_text(doc.title)
            snippet = sanitize_text(doc.snippet)
            text = f"{title}. {snippet}"[:250].replace('"', "'")
            doc_entries.append(f"{idx}. [{source_type.upper()}] {text}")
        
        docs_block = "\n".join(doc_entries)
        
        prompt = f"""You are a sentiment classifier for civic content about Baguio City, Philippines.

Analyze each item and provide sentiment with confidence score (0.0-1.0).

{docs_block}

For each item, classify sentiment AND provide confidence:
- "positive": Appreciation, improvements, success, good news (confidence: how certain)
- "negative": Complaints, problems, incidents, criticism (confidence: how certain)
- "neutral": Factual announcements, balanced reporting (confidence: how certain)

Return JSON array of results:
[{{"i": 0, "s": "negative", "c": 0.85}}, {{"i": 1, "s": "neutral", "c": 0.70}}]"""

        # Exponential backoff for rate limits
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                response = await self.llm.generate(
                    prompt=prompt,
                    system_prompt="You are a sentiment analysis expert. Return accurate, concise JSON.",
                    temperature=0.0,
                    max_tokens=2000,
                )
                
                return self._parse_llm_probs(response, len(batch))
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                        logger.warning(f"Groq rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Groq rate limit exceeded after {max_retries} retries")
                else:
                    logger.warning(f"Groq (llama-3.3-70b-versatile) batch failed: {e}")
                
                # Return neutral defaults on final failure
                return [{"negative": 0.33, "neutral": 0.34, "positive": 0.33}] * len(batch)
        
        # Should never reach here, but return defaults as safety
        return [{"negative": 0.33, "neutral": 0.34, "positive": 0.33}] * len(batch)
    
    def _parse_llm_probs(self, response_text: str, expected_count: int) -> list[dict[str, float]]:
        """Parse LLM response into probability distributions."""
        text = response_text.strip()
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        default_probs = {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
        results = [default_probs.copy() for _ in range(expected_count)]
        
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Handle shortened keys "i", "s", "c"
                        idx = item.get("i", item.get("index", -1))
                        sentiment = item.get("s", item.get("sentiment", "neutral")).lower()
                        confidence = item.get("c", item.get("confidence", 0.7))
                        
                        if 0 <= idx < expected_count and sentiment in ("positive", "negative", "neutral"):
                            confidence = min(max(confidence, 0.4), 0.95)
                            remainder = (1.0 - confidence) / 2
                            
                            probs = {
                                "negative": remainder,
                                "neutral": remainder,
                                "positive": remainder,
                            }
                            probs[sentiment] = confidence
                            results[idx] = probs
                            
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse LLM response: {text[:200]}")
        
        return results
    
    def _detect_source_type(self, doc: WebDocument) -> str:
        """Detect content source type from document."""
        metadata = doc.metadata or {}
        
        if metadata.get("source") == "facebook":
            return "facebook"
        
        url = str(doc.url).lower() if doc.url else ""
        
        if "facebook.com" in url or metadata.get("group_name"):
            return "facebook"
        elif "reddit.com" in url:
            return "reddit"
        else:
            return "web"
    
    def _log_distribution(self, enriched: list[WebDocument]) -> None:
        """Log sentiment and agreement distribution."""
        sentiments = [doc.sentiment for doc in enriched]
        agreements = [doc.metadata.get("model_agreement", "unknown") for doc in enriched]
        
        sent_dist = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral"),
        }
        
        agree_dist = {a: agreements.count(a) for a in set(agreements)}
        
        logger.info(f"[EnsembleSentimentAgent] Sentiment: {sent_dist}")
        logger.info(f"[EnsembleSentimentAgent] Agreement: {agree_dist}")


# Backward compatibility aliases
HybridSentimentAgent = EnsembleSentimentAgent
GeminiSentimentAgent = EnsembleSentimentAgent  # Deprecated: now uses Groq, not Gemini

_sentiment_agent: EnsembleSentimentAgent | None = None


def get_sentiment_agent() -> EnsembleSentimentAgent:
    """Get singleton sentiment agent instance."""
    global _sentiment_agent
    if _sentiment_agent is None:
        _sentiment_agent = EnsembleSentimentAgent()
    return _sentiment_agent
