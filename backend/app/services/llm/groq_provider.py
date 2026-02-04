"""Groq LLM provider with ultra-fast inference (500+ tokens/sec)."""

import json
import logging
import re
from typing import Any, AsyncIterator

from groq import AsyncGroq
from groq.types.chat import ChatCompletion

from ...core.config import get_settings
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider with ultra-fast inference.
    
    Performance characteristics:
    - Speed: 500-800 tokens/sec (10-15x faster than Gemini)
    - Time to First Token: 50-100ms (3-4x faster than Gemini)
    - Context Window: 128K tokens (sufficient for civic analysis)
    - Cost: $0.59/1M tokens (8x more expensive but worth it for speed)
    
    Recommended models:
    - llama-3.3-70b-versatile: Best balance of speed and quality
    - llama-3.1-70b-versatile: Fallback option
    - mixtral-8x7b-32768: Budget option
    - llama-3.1-8b-instant: Simple classification tasks
    """
    
    def __init__(
        self,
        *,
        model: str = "llama-3.3-70b-versatile",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize Groq provider.
        
        Args:
            model: Groq model name
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts on failure
        """
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        
        if self._api_key:
            self._client = AsyncGroq(
                api_key=self._api_key,
                timeout=timeout,
                max_retries=max_retries,
            )
            logger.info(f"[Groq] Initialized with model: {model}")
        else:
            self._client = None
            logger.warning("[Groq] API key not configured")
    
    @property
    def is_available(self) -> bool:
        """Check if Groq is configured."""
        return self._client is not None
    
    @property
    def model_name(self) -> str:
        """Get current model name."""
        return self._model
    
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Generate text with Groq's ultra-fast inference.
        
        Expected latency: 1-3 seconds for 1000 tokens (vs 10-15s with Gemini)
        """
        if not self._client:
            raise RuntimeError("[Groq] Client not initialized (missing API key)")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            completion: ChatCompletion = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = completion.choices[0].message.content
            
            # Log performance metrics
            if hasattr(completion, 'usage') and completion.usage:
                tokens = completion.usage.total_tokens
                prompt_tokens = completion.usage.prompt_tokens
                completion_tokens = completion.usage.completion_tokens
                logger.debug(
                    f"[Groq] Generated {completion_tokens} tokens "
                    f"(prompt: {prompt_tokens}, total: {tokens}) "
                    f"with {self._model}"
                )
            
            return content or ""
            
        except Exception as e:
            logger.error(f"[Groq] Generation failed: {e}")
            
            # Check if fallback is enabled
            settings = get_settings()
            if settings.llm_enable_fallback:
                logger.warning("[Groq] Attempting fallback to Gemini")
                from .factory import get_llm_provider
                fallback = get_llm_provider(settings.llm_fallback_provider)
                return await fallback.generate(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream generation with Groq.
        
        Yields text chunks as they are generated (ultra-fast streaming).
        """
        if not self._client:
            raise RuntimeError("[Groq] Client not initialized (missing API key)")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"[Groq] Streaming failed: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        **kwargs
    ) -> dict[str, Any]:
        """Generate JSON response with Groq.
        
        Uses lower temperature for more consistent JSON output.
        """
        json_prompt = f"""{prompt}

Respond with ONLY valid JSON. No markdown formatting, no explanations."""
        
        raw = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=kwargs.get('max_tokens', 4096),
        )
        
        return self._parse_json(raw)
    
    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Parse JSON from model response with robust error handling."""
        text = raw.strip()
        
        # Strategy 1: Remove markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            text = json_match.group(1).strip()
        
        # Strategy 2: Find JSON object boundaries
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        
        # Strategy 3: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Fix common issues
        try:
            # Remove trailing commas
            fixed = re.sub(r',\s*([}\]])', r'\1', text)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        # Strategy 5: Try to extract partial JSON
        try:
            # Find balanced braces
            depth = 0
            last_valid_end = -1
            for i, char in enumerate(text):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        last_valid_end = i
                        break
            
            if last_valid_end > 0:
                truncated = text[:last_valid_end + 1]
                return json.loads(truncated)
        except json.JSONDecodeError:
            pass
        
        logger.warning(f"[Groq] Failed to parse JSON: {text[:200]}...")
        return {}


# Singleton instance for reuse
_groq_provider: GroqProvider | None = None


def get_groq_provider(model: str = "llama-3.3-70b-versatile") -> GroqProvider:
    """Get or create Groq provider instance.
    
    Args:
        model: Groq model name
        
    Returns:
        Configured Groq provider
    """
    global _groq_provider
    if _groq_provider is None or _groq_provider.model_name != model:
        _groq_provider = GroqProvider(model=model)
    return _groq_provider
