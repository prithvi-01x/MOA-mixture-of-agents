"""
OpenRouter provider implementation using a shared ``httpx.AsyncClient``.

Communicates with the OpenRouter API at https://openrouter.ai/api/v1.
"""

import json
from typing import AsyncGenerator

import httpx

from providers.base import BaseProvider, ProviderError
from providers.retry import async_retry, async_retry_stream

_BASE_URL = "https://openrouter.ai/api/v1"
_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)
_TIMEOUT = httpx.Timeout(60.0)


class OpenRouterProvider(BaseProvider):
    """Concrete provider for the OpenRouter inference gateway."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
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
            raise ProviderError("openrouter", "Invalid API key", 401)
        if code == 429:
            raise ProviderError("openrouter", "Rate limit exceeded", 429)
        if code >= 500:
            raise ProviderError("openrouter", "Server error", code)
        if code >= 400:
            raise ProviderError(
                "openrouter",
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
        """POST /chat/completions (stream=False), return the message content."""
        try:
            payload = self._build_payload(
                model, messages, system_prompt, temperature, max_tokens, stream=False
            )
            response = await self._client.post("/chat/completions", json=payload)
            self._handle_http_error(response)
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            raise ProviderError("openrouter", "Request timed out") from e
        except Exception as e:
            raise ProviderError("openrouter", str(e)) from e

    # ------------------------------------------------------------------
    # Chat (streaming via SSE)
    # ------------------------------------------------------------------

    @async_retry_stream(max_attempts=3, base_delay=1.0)
    async def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """POST /chat/completions (stream=True), yield content deltas."""
        try:
            payload = self._build_payload(
                model, messages, system_prompt, temperature, max_tokens, stream=True
            )
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    await response.aread()
                    self._handle_http_error(response)

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[len("data: "):]

                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content

        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            raise ProviderError("openrouter", "Request timed out") from e
        except Exception as e:
            raise ProviderError("openrouter", str(e)) from e

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    async def list_models(self) -> list[str]:
        """Return popular OpenRouter free-tier models (April 2026)."""
        return [
            "nvidia/nemotron-3-super:free",
            "google/gemma-4-26b-a4b-it:free",
            "qwen/qwen3-coder-480b:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "microsoft/phi-3-medium-128k-instruct:free",
            "openrouter/free",
        ]

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """GET /models — returns True on 200, False otherwise (never raises)."""
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_payload(
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        *,
        stream: bool,
    ) -> dict:
        """Build the JSON payload for /chat/completions."""
        formatted: list[dict[str, str]] = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        formatted.extend(messages)

        return {
            "model": model,
            "messages": formatted,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
