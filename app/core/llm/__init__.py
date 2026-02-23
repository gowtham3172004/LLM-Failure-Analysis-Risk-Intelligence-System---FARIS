"""
FARIS LLM Module

Provides a unified interface for LLM inference that supports multiple backends:
- Ollama (local LLM deployment)
- Google Gemini API (cloud-based)

The provider is selected via the LLM_PROVIDER environment variable.
"""

from typing import Any, Optional, Protocol, runtime_checkable

from app.config import get_settings
from app.core.llm.prompts import PromptTemplates


@runtime_checkable
class LLMClient(Protocol):
    """Protocol defining the interface for LLM clients."""
    
    async def health_check(self) -> bool:
        """Check if the LLM service is available."""
        ...
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Generate text completion."""
        ...
    
    async def generate_structured(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate and parse JSON structured output."""
        ...
    
    async def close(self) -> None:
        """Close the client connection."""
        ...


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get the configured LLM client singleton.
    
    The client type is determined by the LLM_PROVIDER setting:
    - "ollama": Use local Ollama instance
    - "gemini": Use Google Gemini API
    
    Returns:
        LLMClient instance (OllamaClient or GeminiClient)
    """
    global _llm_client
    
    if _llm_client is None:
        settings = get_settings()
        provider = settings.llm_provider.lower()
        
        if provider == "gemini":
            from app.core.llm.gemini import GeminiClient
            _llm_client = GeminiClient()
        else:  # Default to ollama
            from app.core.llm.client import OllamaClient
            _llm_client = OllamaClient()
    
    return _llm_client


async def close_llm_client() -> None:
    """Close the LLM client connection."""
    global _llm_client
    if _llm_client is not None:
        await _llm_client.close()
        _llm_client = None


def reset_llm_client() -> None:
    """Reset the LLM client (useful for testing or switching providers)."""
    global _llm_client
    _llm_client = None


# Re-export for backward compatibility
try:
    from app.core.llm.client import OllamaClient
except ImportError:
    OllamaClient = None  # type: ignore

try:
    from app.core.llm.gemini import GeminiClient
except ImportError:
    GeminiClient = None  # type: ignore

__all__ = [
    "LLMClient",
    "OllamaClient",
    "GeminiClient",
    "get_llm_client",
    "close_llm_client",
    "reset_llm_client",
    "PromptTemplates",
]
