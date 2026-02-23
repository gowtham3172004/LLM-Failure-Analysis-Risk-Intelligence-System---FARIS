"""
FARIS Ollama LLM Client

Async client for local LLM inference using Ollama.
Provides structured output parsing and retry logic.
"""

import json
import re
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings

settings = get_settings()


class OllamaError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when connection to Ollama fails."""
    pass


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama request times out."""
    pass


class OllamaClient:
    """
    Async client for Ollama LLM inference.
    
    Provides:
    - Async generation with streaming support
    - Automatic retries with exponential backoff
    - Structured JSON output parsing
    - Connection health checks
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Ollama API base URL (defaults to settings)
            model: Default model to use (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout
        self.num_ctx = settings.ollama_num_ctx
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10.0),
        )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def health_check(self) -> bool:
        """
        Check if Ollama is running and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> list[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise OllamaConnectionError(f"Failed to list models: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text completion from Ollama.
        
        Args:
            prompt: The prompt to send
            model: Model to use (defaults to client default)
            system: System prompt
            temperature: Generation temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON output format
        
        Returns:
            Generated text response
        
        Raises:
            OllamaError: If generation fails
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.num_ctx,
            },
        }
        
        if system:
            payload["system"] = system
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = await self._client.post(
                "/api/generate",
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
            
        except httpx.TimeoutException:
            raise OllamaTimeoutError(f"Request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            raise OllamaError(f"Generation failed: {e}")
    
    async def generate_structured(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        Generate and parse JSON structured output.
        
        Args:
            prompt: The prompt requesting JSON output
            model: Model to use
            system: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens
        
        Returns:
            Parsed JSON as dictionary
        
        Raises:
            OllamaError: If generation or parsing fails
        """
        response = await self.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        
        try:
            # Try direct JSON parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(
                r"```(?:json)?\s*\n?(.*?)\n?```",
                response,
                re.DOTALL,
            )
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find any JSON object in the response
            json_obj_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_obj_match:
                try:
                    return json.loads(json_obj_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # Last resort: return empty dict with raw response
            return {"_raw_response": response, "_parse_error": True}
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of messages with 'role' and 'content'
            model: Model to use
            temperature: Generation temperature
            max_tokens: Maximum tokens
            json_mode: If True, request JSON format
        
        Returns:
            Assistant's response text
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.num_ctx,
            },
        }
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = await self._client.post(
                "/api/chat",
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("message", {}).get("content", "")
            
        except httpx.TimeoutException:
            raise OllamaTimeoutError(f"Chat request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            raise OllamaError(f"Chat failed: {e}")


# Singleton instance
_llm_client: Optional[OllamaClient] = None


def get_llm_client() -> OllamaClient:
    """
    Get the Ollama client singleton.
    
    Returns:
        OllamaClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = OllamaClient()
    return _llm_client


async def close_llm_client() -> None:
    """Close the LLM client connection."""
    global _llm_client
    if _llm_client is not None:
        await _llm_client.close()
        _llm_client = None
