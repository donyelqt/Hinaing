"""LLM provider factory for multi-provider support."""

import logging
from enum import Enum

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


def get_llm_provider(
    provider: LLMProvider | str = LLMProvider.GROQ,
    *,
    model: str | None = None,
    **kwargs
) -> BaseLLMProvider:
    """Factory function to get LLM provider instance.
    
    This factory enables:
    1. Easy switching between providers (Groq, Gemini, OpenRouter)
    2. Consistent interface across all agents
    3. Automatic fallback on provider failure
    4. A/B testing different providers
    
    Args:
        provider: Provider name (groq, gemini, openrouter)
        model: Optional model override
        **kwargs: Provider-specific configuration
    
    Returns:
        Configured LLM provider instance
        
    Examples:
        >>> # Get Groq provider (fastest)
        >>> llm = get_llm_provider("groq")
        >>> response = await llm.generate("What is the capital of France?")
        
        >>> # Get Gemini provider (highest quality)
        >>> llm = get_llm_provider("gemini", model="gemini-2.5-flash")
        >>> response = await llm.generate("Write a narrative summary...")
        
        >>> # Get with automatic fallback
        >>> from app.core.config import get_settings
        >>> settings = get_settings()
        >>> llm = get_llm_provider(settings.llm_provider_query_orchestrator)
    """
    provider_str = provider.value if isinstance(provider, Enum) else provider

    if provider_str == "groq":
        from .groq_provider import GroqProvider
        return GroqProvider(
            model=model or "llama-3.1-8b-instant",
            **kwargs
        )
    elif provider_str == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider(
            model=model or "gemini-2.5-flash-lite",
            **kwargs
        )
    elif provider_str == "openrouter":
        from ..nlp.openrouter import OpenRouterClient
        # Wrap OpenRouterClient to match BaseLLMProvider interface
        return _wrap_openrouter_client(
            model=model or "deepseek/deepseek-chat",
            **kwargs
        )
    else:
        raise ValueError(f"Unknown provider: {provider_str}")


def get_fast_llm(**kwargs) -> BaseLLMProvider:
    """Get fastest available LLM (Groq preferred).

    Use for:
    - Query planning (Node 1)
    - Sentiment analysis (Node 4)
    - Credibility analysis (Node 4)
    - Theme agents (Node 6)

    Returns:
        Groq provider with Llama 3.1 8B (800+ tokens/sec, cheapest)
    """
    return get_llm_provider(LLMProvider.GROQ, **kwargs)


def get_quality_llm(**kwargs) -> BaseLLMProvider:
    """Get highest quality LLM (Gemini preferred).
    
    Use for:
    - Narrative generation (Node 7)
    - Complex reasoning tasks
    - Long-form content generation
    
    Returns:
        Gemini provider with Flash model
    """
    return get_llm_provider(LLMProvider.GEMINI, **kwargs)


def get_balanced_llm(**kwargs) -> BaseLLMProvider:
    """Get balanced speed/quality LLM.

    Use for:
    - General-purpose tasks
    - When both speed and quality matter

    Returns:
        Groq provider with Llama 3.1 8B (best speed/cost ratio)
    """
    return get_llm_provider(
        LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        **kwargs
    )


def _wrap_openrouter_client(model: str, **kwargs) -> BaseLLMProvider:
    """Wrap OpenRouterClient to match BaseLLMProvider interface.
    
    This is a temporary adapter until OpenRouterClient is refactored
    to inherit from BaseLLMProvider.
    """
    from ..nlp.openrouter import OpenRouterClient
    
    class OpenRouterAdapter(BaseLLMProvider):
        """Adapter to make OpenRouterClient compatible with BaseLLMProvider."""
        
        def __init__(self, model: str, **kwargs):
            self._client = OpenRouterClient(model=model, **kwargs)
        
        @property
        def is_available(self) -> bool:
            return self._client.is_available
        
        @property
        def model_name(self) -> str:
            return self._client._model
        
        async def generate(self, prompt: str, **kwargs):
            return await self._client.generate(prompt, **kwargs)
        
        async def generate_stream(self, prompt: str, **kwargs):
            # OpenRouterClient doesn't support streaming yet
            raise NotImplementedError("Streaming not supported for OpenRouter")
        
        async def generate_json(self, prompt: str, **kwargs):
            return await self._client.generate_json(prompt, **kwargs)
    
    return OpenRouterAdapter(model, **kwargs)


# Provider selection helpers for specific nodes
def get_node_llm(node_name: str, **kwargs) -> BaseLLMProvider:
    """Get LLM provider for a specific node based on configuration.
    
    Args:
        node_name: Node identifier (query_orchestrator, sentiment, credibility, theme_agents, coordinator)
        **kwargs: Provider-specific configuration
    
    Returns:
        Configured LLM provider for the node
        
    Example:
        >>> # In QueryOrchestratorAgent
        >>> llm = get_node_llm("query_orchestrator")
        >>> # Returns Groq if configured, falls back to Gemini
    """
    from ...core.config import get_settings
    settings = get_settings()
    
    # Map node names to config keys
    config_map = {
        "query_orchestrator": settings.llm_provider_query_orchestrator,
        "sentiment": settings.llm_provider_sentiment,
        "credibility": settings.llm_provider_credibility,
        "theme_agents": settings.llm_provider_theme_agents,
        "coordinator": settings.llm_provider_coordinator,
    }
    
    provider = config_map.get(node_name, "groq")
    
    try:
        return get_llm_provider(provider, **kwargs)
    except Exception as e:
        logger.warning(f"Failed to initialize {provider} for {node_name}, falling back to Gemini: {e}")
        return get_llm_provider("gemini", **kwargs)
