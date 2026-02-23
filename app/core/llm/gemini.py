"""
FARIS Gemini LLM Client

Async client for Google's Gemini API for cloud-based LLM inference.
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


class GeminiError(Exception):
    """Base exception for Gemini client errors."""
    pass


class GeminiConnectionError(GeminiError):
    """Raised when connection to Gemini API fails."""
    pass


class GeminiTimeoutError(GeminiError):
    """Raised when Gemini API request times out."""
    pass


class GeminiAuthError(GeminiError):
    """Raised when authentication fails."""
    pass


class GeminiRateLimitError(GeminiError):
    """Raised when rate limit is hit (retryable)."""
    pass


class GeminiClient:
    """
    Async client for Google Gemini API inference.
    
    Provides:
    - Async generation with structured output support
    - Automatic retries with exponential backoff
    - Structured JSON output parsing
    - Connection health checks
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to settings)
            model: Default model to use (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.timeout = timeout or settings.gemini_timeout
        
        if not self.api_key:
            raise GeminiAuthError(
                "Gemini API key not configured. Set GEMINI_API_KEY in your .env file."
            )
        
        self._client = httpx.AsyncClient(
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
        Check if Gemini API is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/models?key={self.api_key}"
            response = await self._client.get(url)
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> list[str]:
        """
        List available models in Gemini.
        
        Returns:
            List of model names
        """
        try:
            url = f"{self.BASE_URL}/models?key={self.api_key}"
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            return [
                model["name"].replace("models/", "") 
                for model in data.get("models", [])
                if "generateContent" in model.get("supportedGenerationMethods", [])
            ]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise GeminiAuthError("Invalid API key")
            raise GeminiConnectionError(f"Failed to list models: {e}")
        except Exception as e:
            raise GeminiConnectionError(f"Failed to list models: {e}")
    
    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=3, min=5, max=60),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, GeminiRateLimitError)),
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
        Generate text completion from Gemini.
        
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
            GeminiError: If generation fails
        """
        model = model or self.model
        
        # Build the content
        contents = []
        
        # Add system instruction via system_instruction parameter
        parts = [{"text": prompt}]
        contents.append({"role": "user", "parts": parts})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            },
        }
        
        # Add system instruction if provided
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }
        
        # Request JSON output
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        
        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"
        
        try:
            response = await self._client.post(url, json=payload)
            
            if response.status_code == 401:
                raise GeminiAuthError("Invalid API key")
            if response.status_code == 403:
                raise GeminiAuthError(f"API key forbidden: {response.text[:200]}")
            if response.status_code == 404:
                raise GeminiError(f"Model '{model}' not found. Available models may have changed. Check GEMINI_MODEL in .env.")
            if response.status_code == 429:
                raise GeminiRateLimitError("Rate limit exceeded. Retrying...")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract text from response
            candidates = data.get("candidates", [])
            if not candidates:
                # Check for prompt feedback (safety blocks)
                feedback = data.get("promptFeedback", {})
                block_reason = feedback.get("blockReason", "")
                if block_reason:
                    return f"[Content blocked by safety filter: {block_reason}]"
                return ""
            
            # Check finish reason
            finish_reason = candidates[0].get("finishReason", "")
            if finish_reason == "SAFETY":
                return "[Content blocked by safety filter]"
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return ""
            
            return parts[0].get("text", "")
            
        except httpx.TimeoutException:
            raise GeminiTimeoutError(f"Request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise GeminiConnectionError("Cannot connect to Gemini API")
        except GeminiError:
            raise
        except Exception as e:
            raise GeminiError(f"Generation failed: {e}")
    
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
            GeminiError: If generation or parsing fails
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
        
        # Convert messages to Gemini format
        contents = []
        system_text = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_text = content
                continue
            
            # Map roles: user -> user, assistant -> model
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            },
        }
        
        if system_text:
            payload["systemInstruction"] = {
                "parts": [{"text": system_text}]
            }
        
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        
        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return ""
            
            return parts[0].get("text", "")
            
        except httpx.TimeoutException:
            raise GeminiTimeoutError(f"Chat request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise GeminiConnectionError("Cannot connect to Gemini API")
        except Exception as e:
            raise GeminiError(f"Chat failed: {e}")


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Get the Gemini client singleton.
    
    Returns:
        GeminiClient instance
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


async def close_gemini_client() -> None:
    """Close the Gemini client connection."""
    global _gemini_client
    if _gemini_client is not None:
        await _gemini_client.close()
        _gemini_client = None
