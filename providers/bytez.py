"""
Bytez provider implementation using a shared ``httpx.AsyncClient``.

Bytez does not support native streaming — ``stream()`` simulates it by
calling ``chat()`` and yielding the complete response as a single chunk.
"""

from typing import AsyncGenerator

import httpx

from providers.base import BaseProvider, ProviderError
from providers.retry import async_retry

_BASE_URL = "https://api.bytez.com/model/v2"
_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)
_TIMEOUT = httpx.Timeout(30.0)


class BytezProvider(BaseProvider):
    """Concrete provider for the Bytez inference API."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }
        # Shared client — reused across all requests to this provider
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers=self._headers,
            limits=_LIMITS,
            timeout=_TIMEOUT,
        )

    async def aclose(self) -> None:
        """Close the shared httpx client on application shutdown."""
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Error handling helper
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_http_error(response: httpx.Response) -> None:
        """Raise a ProviderError for known HTTP error codes."""
        code = response.status_code
        if code == 401:
            raise ProviderError("bytez", "Invalid API key", 401)
        if code == 404:
            raise ProviderError("bytez", "Model not found", 404)
        if code >= 400:
            raise ProviderError(
                "bytez",
                f"Request failed: {response.text}",
                code,
            )

    # ------------------------------------------------------------------
    # Chat (non-streaming)
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3, base_delay=1.0)
    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """POST to Bytez inference endpoint, return generated text."""
        try:
            formatted = self._build_messages(messages, system_prompt)
            payload = {
                "messages": formatted,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            }

            response = await self._client.post(f"/{model}", json=payload)
            self._handle_http_error(response)
            data = response.json()
            return data["output"][0]["generated_text"]

        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            raise ProviderError("bytez", "Model timed out - cold start?") from e
        except Exception as e:
            raise ProviderError("bytez", str(e)) from e

    # ------------------------------------------------------------------
    # Simulated streaming
    # ------------------------------------------------------------------

    async def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Simulate streaming by calling chat() and yielding the full response
        as a single content chunk.
        """
        content = await self.chat(
            model=model,
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        yield content

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    async def list_models(self) -> list[str]:
        """Return an empty list — users provide Bytez model names manually."""
        return []

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Return True if an API key is configured, False otherwise."""
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        """Prepend a system message if a system_prompt is provided."""
        formatted: list[dict[str, str]] = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        formatted.extend(messages)
        return formatted
