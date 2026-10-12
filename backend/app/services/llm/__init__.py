"""LLM abstraction layer: Groq (cloud) and Ollama/Qwen (local)."""

from .base import BaseLLMProvider
from .factory import (
    PROVIDER_GROQ,
    PROVIDER_LOCAL,
    SUPPORTED_PROVIDERS,
    get_llm_for_mode,
    get_llm_provider,
)
from .langchain_adapter import ProviderChatModel
from .mode import (
    CLOUD,
    LOCAL,
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

__all__ = [
    "BaseLLMProvider",
    "PROVIDER_GROQ",
    "PROVIDER_LOCAL",
    "SUPPORTED_PROVIDERS",
    "get_llm_provider",
    "get_llm_for_mode",
    "ProviderChatModel",
    "OllamaProvider",
    "get_ollama_provider",
    "clear_ollama_cache",
    "CLOUD",
    "LOCAL",
    "VALID_LLM_MODES",
    "InvalidLLMMode",
    "default_llm_mode",
    "describe_active_llm",
    "get_active_llm_mode",
    "llm_mode_scope",
    "normalize_llm_mode",
    "provider_name_for_mode",
]
