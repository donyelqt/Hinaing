"""AI-based sentiment analysis agent using Gemini."""
from __future__ import annotations

import json
import logging
from typing import Literal

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from ...schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "negative", "neutral"]

# Disable safety filters for civic news analysis (legitimate news content)
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class GeminiSentimentAgent:
    """AI-powered sentiment analysis using Gemini for accurate classification."""
    
    def __init__(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.batch_size = 5  # Smaller batches for reliability
        logger.info("GeminiSentimentAgent initialized")
    
    def analyze_single(self, text: str) -> SentimentLabel:
        """Analyze sentiment of a single text."""
        prompt = self._build_single_prompt(text)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=10,
                ),
                safety_settings=SAFETY_SETTINGS,
            )
            
            # Handle blocked or empty responses
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning("Gemini returned empty response, using fallback")
                return self._fallback_sentiment(text)
            
            result = response.text.strip().lower()
            
            if result in ("positive", "negative", "neutral"):
                return result
            
            if "positive" in result:
                return "positive"
            elif "negative" in result:
                return "negative"
            return "neutral"
            
        except Exception as e:
            logger.warning(f"Gemini sentiment failed, using fallback: {e}")
            return self._fallback_sentiment(text)
    
    def _build_single_prompt(self, text: str) -> str:
        """Build prompt for single text analysis."""
        return f"""You are a sentiment classifier for civic news about Baguio City, Philippines.

Analyze this text and classify the PUBLIC SENTIMENT it represents:

Text: "{text[:500]}"

Classification rules:
- "positive": Community appreciation, improvements, success stories, resolved issues, good news
- "negative": Public complaints, concerns, problems, risks, incidents, delays, criticism
- "neutral": Factual announcements, balanced reporting, informational content

Respond with exactly ONE word: positive, negative, or neutral"""

    def analyze_batch(self, documents: list[WebDocument]) -> list[WebDocument]:
        """Analyze sentiment for a batch of documents efficiently."""
        if not documents:
            return []
        
        logger.info(f"[GeminiSentimentAgent] Analyzing {len(documents)} documents")
        
        enriched: list[WebDocument] = []
        
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_results = self._analyze_batch_internal(batch)
            enriched.extend(batch_results)
        
        # Log sentiment distribution
        sentiments = [doc.sentiment for doc in enriched]
        dist = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral"),
        }
        logger.info(f"[GeminiSentimentAgent] Sentiment distribution: {dist}")
        
        return enriched
    
    def _analyze_batch_internal(self, batch: list[WebDocument]) -> list[WebDocument]:
        """Analyze a batch of documents in a single API call."""
        doc_entries = []
        for idx, doc in enumerate(batch):
            # Sanitize text to avoid triggering safety filters
            text = f"{doc.title}. {doc.snippet}"[:250]
            text = text.replace('"', "'")  # Avoid quote issues
            doc_entries.append(f"{idx}. {text}")
        
        docs_block = "\n".join(doc_entries)
        
        prompt = f"""You are a sentiment classifier for civic news about Baguio City, Philippines.

Classify the PUBLIC SENTIMENT for each numbered news item:

{docs_block}

Classification rules:
- "positive": Community appreciation, improvements, success, good news
- "negative": Public complaints, concerns, problems, incidents, criticism
- "neutral": Factual announcements, balanced reporting, informational

Return ONLY a JSON array (no markdown):
[{{"index": 0, "sentiment": "negative"}}, {{"index": 1, "sentiment": "neutral"}}]"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=300,
                ),
                safety_settings=SAFETY_SETTINGS,
            )
            
            # Handle blocked or empty responses
            if not response.candidates:
                logger.warning("Gemini batch returned no candidates, using fallback")
                return self._fallback_batch(batch)
            
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                # Check if blocked by safety
                if candidate.finish_reason and candidate.finish_reason.name == "SAFETY":
                    logger.warning("Gemini batch blocked by safety filter, using fallback")
                else:
                    logger.warning("Gemini batch returned empty content, using fallback")
                return self._fallback_batch(batch)
            
            results = self._parse_batch_response(response.text, len(batch))
            
            enriched = []
            for idx, doc in enumerate(batch):
                sentiment = results.get(idx, self._fallback_sentiment(doc.snippet))
                enriched.append(doc.model_copy(update={"sentiment": sentiment}))
            
            return enriched
            
        except Exception as e:
            logger.warning(f"Batch sentiment failed, using fallback: {e}")
            return self._fallback_batch(batch)
    
    def _fallback_batch(self, batch: list[WebDocument]) -> list[WebDocument]:
        """Apply fallback sentiment to entire batch."""
        return [
            doc.model_copy(update={"sentiment": self._fallback_sentiment(doc.snippet or doc.title)})
            for doc in batch
        ]
    
    def _parse_batch_response(self, response_text: str, expected_count: int) -> dict[int, SentimentLabel]:
        """Parse batch response JSON."""
        text = response_text.strip()
        
        # Extract JSON if wrapped in markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            data = json.loads(text)
            if isinstance(data, list):
                results = {}
                for item in data:
                    if isinstance(item, dict):
                        idx = item.get("index", -1)
                        sentiment = item.get("sentiment", "neutral").lower()
                        if sentiment in ("positive", "negative", "neutral"):
                            results[idx] = sentiment
                return results
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse batch response: {text[:200]}")
        
        return {}
    
    def _fallback_sentiment(self, text: str) -> SentimentLabel:
        """Rule-based fallback when Gemini fails."""
        if not text:
            return "neutral"
            
        lowered = text.lower()
        
        positive_hints = {
            "improved", "great", "excellent", "success", "appreciate", "happy", 
            "resolved", "good news", "achievement", "progress", "completed",
            "inaugurated", "launched", "celebrated", "awarded"
        }
        negative_hints = {
            "delay", "problem", "issue", "concern", "warning", "outage", 
            "flood", "traffic", "risk", "accident", "crime", "complaint",
            "protest", "oppose", "reject", "failed", "crisis", "emergency"
        }
        
        pos_hits = sum(word in lowered for word in positive_hints)
        neg_hits = sum(word in lowered for word in negative_hints)
        
        if neg_hits > pos_hits:
            return "negative"
        if pos_hits > neg_hits:
            return "positive"
        return "neutral"


# Singleton instance
_sentiment_agent: GeminiSentimentAgent | None = None


def get_sentiment_agent() -> GeminiSentimentAgent:
    """Get singleton sentiment agent instance."""
    global _sentiment_agent
    if _sentiment_agent is None:
        _sentiment_agent = GeminiSentimentAgent()
    return _sentiment_agent
