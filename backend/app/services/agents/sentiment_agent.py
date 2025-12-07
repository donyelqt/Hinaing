"""Full Ensemble Sentiment Analysis using RoBERTa + Gemini.

Both models analyze ALL documents, predictions are combined for maximum accuracy.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Literal

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from ...schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "negative", "neutral"]

# Disable safety filters for civic news analysis
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Ensemble weights (sum to 1.0)
ROBERTA_WEIGHT = 0.4   # Transformer model weight
GEMINI_WEIGHT = 0.6    # LLM weight (higher because context-aware)


def sanitize_text(text: str | None) -> str:
    """Remove invalid Unicode characters (surrogates) that break APIs.
    
    The character \ud835 and similar surrogates cause:
    - UnicodeEncodeError in Gemini API
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
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
        self.model.eval()
        
        # Model outputs: 0=negative, 1=neutral, 2=positive
        self.label_map = {0: "negative", 1: "neutral", 2: "positive"}
        
        logger.info("RoBERTa sentiment model loaded")
    
    def predict_batch_with_probs(self, texts: list[str]) -> list[dict[str, float]]:
        """Get probability distributions for batch of texts."""
        if not texts:
            return []
        
        # Sanitize and validate texts
        sanitized = []
        for t in texts:
            clean = sanitize_text(t)
            # Ensure non-empty string for tokenizer
            if not clean:
                clean = "neutral content"
            sanitized.append(clean[:512])
        
        try:
            inputs = self.tokenizer(
                sanitized,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            results = []
            for prob in probs:
                results.append({
                    "negative": prob[0].item(),
                    "neutral": prob[1].item(),
                    "positive": prob[2].item(),
                })
            
            return results
            
        except Exception as e:
            logger.warning(f"RoBERTa batch failed: {e}")
            # Return neutral for all on failure
            return [{"negative": 0.33, "neutral": 0.34, "positive": 0.33}] * len(texts)


@lru_cache(maxsize=1)
def get_sentiment_model() -> RoBERTaSentimentModel:
    """Get singleton sentiment model instance."""
    return RoBERTaSentimentModel()


class EnsembleSentimentAgent:
    """Full Ensemble: RoBERTa + Gemini analyze ALL documents."""
    
    def __init__(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-pro")
        self.roberta = get_sentiment_model()
        self.batch_size = 8
        
        logger.info(
            f"EnsembleSentimentAgent initialized "
            f"(RoBERTa weight={ROBERTA_WEIGHT}, Gemini weight={GEMINI_WEIGHT})"
        )
    
    def analyze_batch(self, documents: list[WebDocument]) -> list[WebDocument]:
        """Analyze sentiment using full ensemble of both models."""
        if not documents:
            return []
        
        logger.info(f"[EnsembleSentimentAgent] Analyzing {len(documents)} documents with full ensemble")
        
        # Sanitize texts before processing
        texts = []
        for doc in documents:
            title = sanitize_text(doc.title)
            snippet = sanitize_text(doc.snippet)
            texts.append(f"{title}. {snippet}"[:512])
        
        # Run RoBERTa and Gemini in PARALLEL for speed
        logger.info("[EnsembleSentimentAgent] Running RoBERTa + Gemini in parallel...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            roberta_future = executor.submit(self.roberta.predict_batch_with_probs, texts)
            gemini_future = executor.submit(self._gemini_analyze_all, documents)
            
            roberta_probs = roberta_future.result()
            gemini_probs = gemini_future.result()
        
        # Step 3: Combine predictions with weighted ensemble
        enriched: list[WebDocument] = []
        
        for idx, doc in enumerate(documents):
            r_probs = roberta_probs[idx]
            g_probs = gemini_probs[idx]
            
            # Weighted combination
            combined = {
                "negative": (ROBERTA_WEIGHT * r_probs["negative"]) + (GEMINI_WEIGHT * g_probs["negative"]),
                "neutral": (ROBERTA_WEIGHT * r_probs["neutral"]) + (GEMINI_WEIGHT * g_probs["neutral"]),
                "positive": (ROBERTA_WEIGHT * r_probs["positive"]) + (GEMINI_WEIGHT * g_probs["positive"]),
            }
            
            final_label = max(combined, key=combined.get)
            final_confidence = combined[final_label]
            
            roberta_label = max(r_probs, key=r_probs.get)
            gemini_label = max(g_probs, key=g_probs.get)
            
            if roberta_label == gemini_label:
                agreement = "full_agreement"
            elif final_label == roberta_label:
                agreement = "roberta_dominant"
            elif final_label == gemini_label:
                agreement = "gemini_dominant"
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
                    "gemini_prediction": gemini_label,
                    "gemini_confidence": round(max(g_probs.values()), 3),
                    "model_agreement": agreement,
                    "content_source_type": source_type,
                }
            }))
        
        self._log_distribution(enriched)
        return enriched
    
    def _gemini_analyze_all(self, documents: list[WebDocument]) -> list[dict[str, float]]:
        """Get Gemini probability distributions for all documents."""
        all_probs: list[dict[str, float]] = []
        
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_probs = self._gemini_batch_with_probs(batch)
            all_probs.extend(batch_probs)
        
        return all_probs
    
    def _gemini_batch_with_probs(self, batch: list[WebDocument]) -> list[dict[str, float]]:
        """Get Gemini predictions with confidence scores."""
        doc_entries = []
        for idx, doc in enumerate(batch):
            source_type = self._detect_source_type(doc)
            # Sanitize text before sending to Gemini
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

Return JSON array with sentiment AND confidence for each:
[{{"index": 0, "sentiment": "negative", "confidence": 0.85}}, {{"index": 1, "sentiment": "neutral", "confidence": 0.70}}]"""

        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500,
                ),
                safety_settings=SAFETY_SETTINGS,
            )
            
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning("Gemini returned empty response")
                return [{"negative": 0.33, "neutral": 0.34, "positive": 0.33}] * len(batch)
            
            return self._parse_gemini_probs(response.text, len(batch))
            
        except Exception as e:
            logger.warning(f"Gemini batch failed: {e}")
            return [{"negative": 0.33, "neutral": 0.34, "positive": 0.33}] * len(batch)
    
    def _parse_gemini_probs(self, response_text: str, expected_count: int) -> list[dict[str, float]]:
        """Parse Gemini response into probability distributions."""
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
                        idx = item.get("index", -1)
                        sentiment = item.get("sentiment", "neutral").lower()
                        confidence = item.get("confidence", 0.7)
                        
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
            logger.debug(f"Failed to parse Gemini response: {text[:200]}")
        
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
GeminiSentimentAgent = EnsembleSentimentAgent

_sentiment_agent: EnsembleSentimentAgent | None = None


def get_sentiment_agent() -> EnsembleSentimentAgent:
    """Get singleton sentiment agent instance."""
    global _sentiment_agent
    if _sentiment_agent is None:
        _sentiment_agent = EnsembleSentimentAgent()
    return _sentiment_agent
