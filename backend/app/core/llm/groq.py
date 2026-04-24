"""
FARIS Groq LLM Client

Async client for Groq's OpenAI-compatible API.
Provides structured output parsing and retry logic.
"""

import json
import re
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

settings = get_settings()


class GroqError(Exception):
    """Base exception for Groq client errors."""


class GroqConnectionError(GroqError):
    """Raised when connection to Groq API fails."""


class GroqTimeoutError(GroqError):
    """Raised when Groq API request times out."""


class GroqAuthError(GroqError):
    """Raised when authentication fails."""


class GroqRateLimitError(GroqError):
    """Raised when rate limit is hit (retryable)."""


class GroqServiceUnavailableError(GroqError):
    """Raised when Groq service is temporarily unavailable (retryable)."""


class GroqClient:
    """
    Async client for Groq API inference.

    Provides:
    - Async generation with structured output support
    - Automatic retries with exponential backoff
    - Structured JSON output parsing
    - Connection health checks
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the Groq client.

        Args:
            api_key: Groq API key (defaults to settings)
            base_url: Groq API base URL (defaults to settings)
            model: Default model to use (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.api_key = api_key or settings.groq_api_key
        self.base_url = base_url or settings.groq_base_url
        self.model = model or settings.groq_model
        self.timeout = timeout or settings.groq_timeout

        if not self.api_key:
            raise GroqAuthError(
                "Groq API key not configured. Set GROQ_API_KEY in your .env file."
            )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
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
        Check if Groq API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """
        List available models in Groq.

        Returns:
            List of model IDs
        """
        try:
            response = await self._client.get("/models")
            response.raise_for_status()
            data = response.json()
            return [model.get("id", "") for model in data.get("data", []) if model.get("id")]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise GroqAuthError("Invalid Groq API key")
            raise GroqConnectionError(f"Failed to list models: {e}")
        except Exception as e:
            raise GroqConnectionError(f"Failed to list models: {e}")

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=3, min=5, max=60),
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.ConnectError,
                GroqRateLimitError,
                GroqServiceUnavailableError,
            )
        ),
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
        Generate text completion from Groq.

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
            GroqError: If generation fails
        """
        model = model or self.model

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.post("/chat/completions", json=payload)

            if response.status_code in (401, 403):
                raise GroqAuthError("Invalid or unauthorized Groq API key")
            if response.status_code == 404:
                raise GroqError(f"Model '{model}' not found. Check GROQ_MODEL in .env.")
            if response.status_code == 429:
                raise GroqRateLimitError("Rate limit exceeded. Retrying...")
            if response.status_code in (502, 503, 504):
                raise GroqServiceUnavailableError(
                    f"Groq service unavailable ({response.status_code}). Retrying..."
                )

            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return ""

            message = choices[0].get("message", {})
            return message.get("content", "") or ""

        except httpx.TimeoutException:
            raise GroqTimeoutError(f"Request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise GroqConnectionError("Cannot connect to Groq API")
        except GroqError:
            raise
        except Exception as e:
            raise GroqError(f"Generation failed: {e}")

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
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            json_obj_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_obj_match:
                try:
                    return json.loads(json_obj_match.group(0))
                except json.JSONDecodeError:
                    pass

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

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return ""

            return choices[0].get("message", {}).get("content", "") or ""

        except httpx.TimeoutException:
            raise GroqTimeoutError(f"Chat request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise GroqConnectionError("Cannot connect to Groq API")
        except Exception as e:
            raise GroqError(f"Chat failed: {e}")


# Singleton instance
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """
    Get the Groq client singleton.

    Returns:
        GroqClient instance
    """
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client


async def close_groq_client() -> None:
    """Close the Groq client connection."""
    global _groq_client
    if _groq_client is not None:
        await _groq_client.close()
        _groq_client = None
