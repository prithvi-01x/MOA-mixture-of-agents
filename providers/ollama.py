"""
Ollama provider implementation using a shared ``httpx.AsyncClient``.

Connects to a local (or remote) Ollama instance via direct HTTP calls,
avoiding the threading issues of ``ollama.AsyncClient`` under asyncio.gather.
"""

import json
import os
from typing import AsyncGenerator

import httpx

from providers.base import BaseProvider, ProviderError
from providers.retry import async_retry, async_retry_stream

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)
_TIMEOUT = httpx.Timeout(30.0)


class OllamaProvider(BaseProvider):
    """Concrete provider backed by an Ollama server."""

    def __init__(self) -> None:
        self.base_url = OLLAMA_BASE_URL
        # Shared client — reused across all requests to this provider
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            limits=_LIMITS,
            timeout=_TIMEOUT,
        )

    async def aclose(self) -> None:
        """Close the shared httpx client on application shutdown."""
        await self._client.aclose()

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
        """Send a chat request and return the full response content."""
        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": model,
                    "messages": self._build_messages(messages, system_prompt),
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(provider="ollama", message=str(e)) from e

    # ------------------------------------------------------------------
    # Chat (streaming)
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
        """Stream chat tokens line-by-line from the Ollama streaming API."""
        try:
            async with self._client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": model,
                    "messages": self._build_messages(messages, system_prompt),
                    "stream": True,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(provider="ollama", message=str(e)) from e

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    async def list_models(self) -> list[str]:
        """Return a list of model name strings available on the Ollama server."""
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["model"] for model in data.get("models", [])]
        except Exception as e:
            raise ProviderError(provider="ollama", message=str(e)) from e

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """GET ``/api/tags`` — True if the server responds 200, False otherwise."""
        try:
            resp = await self._client.get("/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

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
