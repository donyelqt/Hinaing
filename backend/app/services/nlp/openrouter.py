"""OpenRouter client for accessing multiple LLM providers.

This module provides a unified interface to OpenRouter API, supporting:
- DeepSeek Chat (recommended Gemini alternative)
- Qwen QwQ 32B (strong reasoning)
- Gemma 2 27B (Google's open model)
- Mistral Small 3 (fast inference)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable

import httpx

from ...core.config import get_settings

logger = logging.getLogger(__name__)


# Recommended models (free tier available)
OPENROUTER_MODELS = {
    "fast": "deepseek/deepseek-chat",        # Best all-around, most Gemini-like
    "reasoning": "qwen/qwq-32b",              # Strong reasoning for complex tasks
    "google": "google/gemma-2-27b-it",        # Google's official model
    "mistral": "mistralai/mistral-small-3.1-24-02",  # Fast, efficient
}


class OpenRouterClient:
    """Unified client for OpenRouter API with automatic retries and fallback."""

    def __init__(
        self,
        *,
        model: str = "deepseek/deepseek-chat",
        timeout: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        """Initialize OpenRouter client.
        
        Args:
            model: OpenRouter model ID (default: deepseek/deepseek-chat)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts on failure
        """
        settings = get_settings()
        self._api_key = settings.openrouter_api_key or settings.gemini_api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._base_url = "https://openrouter.ai/api/v1"
        
        if not self._api_key:
            logger.warning("No OpenRouter API key configured")
            self._client: httpx.AsyncClient | None = None
        else:
            self._client = httpx.AsyncClient(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hinaing.app",
                    "X-Title": "Hinaing Civic Analysis",
                },
            )

    @property
    def is_available(self) -> bool:
        return self._client is not None and bool(self._api_key)

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text using OpenRouter.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum output tokens
            
        Returns:
            Generated text response
        """
        if not self._client:
            raise RuntimeError("OpenRouter client not initialized (no API key)")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"OpenRouter rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"OpenRouter API error: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"OpenRouter request failed: {e}")
                if attempt < self._max_retries:
                    await asyncio.sleep(1)
                    continue
                raise

        raise RuntimeError("OpenRouter request failed after retries")

    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate JSON response using OpenRouter.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Lower temperature for more consistent JSON
            
        Returns:
            Parsed JSON response as dict
        """
        json_prompt = f"""{prompt}

Respond with ONLY valid JSON. No markdown formatting, no explanations.
"""
        raw = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=4096,
        )
        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Parse JSON from model response."""
        text = raw.strip()
        
        # Remove markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            text = json_match.group(1).strip()
        
        # Find JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to fix common issues
            fixed = re.sub(r',\s*([}\]])', r'\1', text)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON: {text[:200]}...")
                return {}


# Convenience functions for specific use cases
async def generate_narrative(
    context: str,
    *,
    model: str = "deepseek/deepseek-chat",
) -> str:
    """Generate a narrative summary from documents."""
    client = OpenRouterClient(model=model)
    prompt = f"""You are a civic analyst for Baguio City. Based on the following documents, generate a comprehensive narrative summary:

{context}

Write 4-6 paragraphs covering the key themes, sentiment, and actionable insights. Format as prose, not bullet points."""
    
    return await client.generate(
        prompt=prompt,
        system_prompt="You are a senior civic analyst. Generate clear, engaging narratives.",
        temperature=0.3,
    )


async def analyze_sentiment(
    documents: list[dict[str, Any]],
    *,
    model: str = "deepseek/deepseek-chat",
) -> dict[str, Any]:
    """Analyze sentiment across documents."""
    client = OpenRouterClient(model=model)
    
    doc_text = "\n".join(
        f"- [{d.get('sentiment', 'neutral')}] {d.get('title', '')}: {d.get('snippet', '')[:200]}"
        for d in documents[:50]
    )
    
    prompt = f"""Analyze the sentiment of these Baguio City documents:

{doc_text}

Return JSON with:
- overall_sentiment: "positive", "negative", "neutral", or "mixed"
- summary: 2-3 sentence summary
- key_themes: array of theme names
- notable_points: array of interesting findings"""
    
    return await client.generate_json(
        prompt=prompt,
        system_prompt="You are a sentiment analysis expert. Return accurate, concise JSON.",
    )


# Global instance (lazy initialization)
_openrouter_client: OpenRouterClient | None = None


def get_openrouter_client(model: str = "deepseek/deepseek-chat") -> OpenRouterClient:
    """Get or create OpenRouter client instance."""
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient(model=model)
    return _openrouter_client
