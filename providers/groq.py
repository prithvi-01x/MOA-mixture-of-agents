"""
Groq provider — OpenAI-compatible API via api.groq.com.
Free tier: generous rate limits, extremely fast inference.
"""

import json
from typing import AsyncGenerator

import httpx

from providers.base import BaseProvider, ProviderError
from providers.retry import async_retry, async_retry_stream

_BASE_URL = "https://api.groq.com/openai/v1"
_LIMITS  = httpx.Limits(max_connections=20, max_keepalive_connections=10)
_TIMEOUT = httpx.Timeout(60.0)


class GroqProvider(BaseProvider):
    """Concrete provider for the Groq inference API."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers=self._headers,
            limits=_LIMITS,
            timeout=_TIMEOUT,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _handle_http_error(response: httpx.Response) -> None:
        code = response.status_code
        if code == 401:
            raise ProviderError("groq", "Invalid API key", 401)
        if code == 429:
            raise ProviderError("groq", "Rate limit exceeded", 429)
        if code >= 500:
            raise ProviderError("groq", "Server error", code)
        if code >= 400:
            raise ProviderError("groq", f"Request failed: {response.text}", code)

    @async_retry(max_attempts=3, base_delay=1.0)
    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        try:
            payload = self._build_payload(model, messages, system_prompt,
                                          temperature, max_tokens, stream=False)
            response = await self._client.post("/chat/completions", json=payload)
            self._handle_http_error(response)
            return response.json()["choices"][0]["message"]["content"]
        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            raise ProviderError("groq", "Request timed out") from e
        except Exception as e:
            raise ProviderError("groq", str(e)) from e

    @async_retry_stream(max_attempts=3, base_delay=1.0)
    async def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        try:
            payload = self._build_payload(model, messages, system_prompt,
                                          temperature, max_tokens, stream=True)
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
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
                    content = choices[0].get("delta", {}).get("content")
                    if content:
                        yield content
        except ProviderError:
            raise
        except httpx.TimeoutException as e:
            raise ProviderError("groq", "Request timed out") from e
        except Exception as e:
            raise ProviderError("groq", str(e)) from e

    async def list_models(self) -> list[str]:
        """Return popular Groq free-tier models (April 2026)."""
        return [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
            "groq/compound",
            "groq/compound-mini",
        ]

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

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
