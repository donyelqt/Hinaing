"""LLM abstraction layer: Groq (cloud), Ollama/Qwen (local), OpenRouter gateway."""

from .base import BaseLLMProvider
from .factory import (
    PROVIDER_GROQ,
    PROVIDER_LOCAL,
    PROVIDER_OPENROUTER,
    SUPPORTED_PROVIDERS,
    get_llm_for_mode,
    get_llm_provider,
)
from .langchain_adapter import ProviderChatModel
from .mode import (
    CLOUD,
    LOCAL,
    OPENROUTER,
    VALID_LLM_MODES,
    InvalidLLMMode,
    default_llm_mode,
    describe_active_llm,
    get_active_llm_mode,
    llm_mode_scope,
    normalize_llm_mode,
    provider_name_for_mode,
)
from .ollama_provider import (
    OllamaProvider,
    get_ollama_provider,
    clear_ollama_cache,
)
from .openrouter_provider import OpenRouterProvider, get_openrouter_provider

__all__ = [
    "BaseLLMProvider",
    "PROVIDER_GROQ",
    "PROVIDER_LOCAL",
    "PROVIDER_OPENROUTER",
    "SUPPORTED_PROVIDERS",
    "get_llm_provider",
    "get_llm_for_mode",
    "ProviderChatModel",
    "OllamaProvider",
    "get_ollama_provider",
    "clear_ollama_cache",
    "OpenRouterProvider",
    "get_openrouter_provider",
    "CLOUD",
    "LOCAL",
    "OPENROUTER",
    "VALID_LLM_MODES",
    "InvalidLLMMode",
    "default_llm_mode",
    "describe_active_llm",
    "get_active_llm_mode",
    "llm_mode_scope",
    "normalize_llm_mode",
    "provider_name_for_mode",
]
