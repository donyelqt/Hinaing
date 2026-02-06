"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseLLMProvider(ABC):
    """Abstract base for LLM providers (Groq, Gemini, OpenRouter).
    
    This abstraction enables:
    1. Provider-agnostic agent code
    2. Easy A/B testing between providers
    3. Automatic fallback on provider failure
    4. Consistent interface across sync/async operations
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Generate text completion.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum output tokens
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming completion.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum output tokens
            **kwargs: Provider-specific parameters
            
        Yields:
            Text chunks as they are generated
        """
        pass
    
    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        **kwargs
    ) -> dict[str, Any]:
        """Generate JSON response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Lower temperature for consistent JSON
            **kwargs: Provider-specific parameters
            
        Returns:
            Parsed JSON response as dict
        """
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available.
        
        Returns:
            True if provider has valid API key and is ready to use
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get current model name.
        
        Returns:
            Model identifier (e.g., "llama-3.3-70b-versatile")
        """
        pass
