"""Gemini LLM provider wrapper (refactored from existing code)."""

import json
import logging
import re
from typing import Any, AsyncIterator

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Disable safety filters for civic news analysis
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider for high-quality generation.
    
    Performance characteristics:
    - Speed: 40-60 tokens/sec (baseline)
    - Time to First Token: 200-400ms
    - Context Window: 1M tokens (excellent for long context)
    - Cost: $0.075/1M tokens (cost-effective)
    
    Recommended models:
    - gemini-2.5-flash-lite: Fast, balanced (default)
    - gemini-2.5-flash: Higher quality
    - gemma-3-27b: Open model alternative
    """
    
    def __init__(
        self,
        *,
        model: str = "gemini-2.5-flash-lite",
        timeout: float = 60.0,
    ):
        """Initialize Gemini provider.
        
        Args:
            model: Gemini model name
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        self._model_name = model
        self._timeout = timeout
        self._model = None
        
        if self._api_key:
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                self._model_name,
                safety_settings=SAFETY_SETTINGS,
            )
            logger.info(f"[Gemini] Initialized with model: {model}")
        else:
            logger.warning("[Gemini] API key not configured")
    
    @property
    def is_available(self) -> bool:
        """Check if Gemini is configured."""
        return self._model is not None
    
    @property
    def model_name(self) -> str:
        """Get current model name."""
        return self._model_name
    
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Generate text with Gemini."""
        if not self._model:
            raise RuntimeError("[Gemini] Client not initialized (missing API key)")
        
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self._model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                request_options={"timeout": self._timeout},
            )
            
            # Handle response validation
            if not response.candidates:
                logger.warning(f"[Gemini] No candidates returned. Feedback: {response.prompt_feedback}")
                return ""
            
            candidate = response.candidates[0]
            
            # Check finish reason
            if candidate.finish_reason != 1:  # 1 = STOP (successful)
                finish_reason_map = {1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}
                reason = finish_reason_map.get(candidate.finish_reason, f"UNKNOWN({candidate.finish_reason})")
                logger.warning(f"[Gemini] Finished with reason: {reason}")
            
            # Check content parts
            if not candidate.content.parts:
                logger.warning("[Gemini] Empty content parts")
                return ""
            
            return response.text or ""
            
        except Exception as e:
            logger.error(f"[Gemini] Generation failed: {e}")
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
        """Stream generation with Gemini."""
        if not self._model:
            raise RuntimeError("[Gemini] Client not initialized (missing API key)")
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self._model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=True,
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"[Gemini] Streaming failed: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        **kwargs
    ) -> dict[str, Any]:
        """Generate JSON response with Gemini."""
        json_prompt = f"""{prompt}

Return ONLY valid JSON. No markdown formatting, no explanations."""
        
        raw = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=kwargs.get('max_tokens', 4096),
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
                logger.warning(f"[Gemini] Failed to parse JSON: {text[:200]}...")
                return {}


# Singleton instance
_gemini_provider: GeminiProvider | None = None


def get_gemini_provider(model: str = "gemini-2.5-flash-lite") -> GeminiProvider:
    """Get or create Gemini provider instance."""
    global _gemini_provider
    if _gemini_provider is None or _gemini_provider.model_name != model:
        _gemini_provider = GeminiProvider(model=model)
    return _gemini_provider
