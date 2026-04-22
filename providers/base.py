"""
Abstract base provider and shared data structures for the MOA provider layer.

All concrete providers (Groq, OpenRouter, etc.) must subclass
``BaseProvider`` and implement its abstract methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class ProviderError(Exception):
    """Raised when a provider encounters an error."""

    def __init__(
        self,
        provider: str,
        message: str,
        status_code: int | None = None,
    ) -> None:
        self.provider = provider
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{provider}] {message} (status={status_code})")


@dataclass
class StreamChunk:
    """A single chunk emitted during a streaming response."""

    content: str
    model: str
    provider: str
    is_done: bool = False


@dataclass
class SpecialistResult:
    """The completed result returned by a specialist model invocation."""

    model: str
    provider: str
    content: str
    tokens_per_sec: float
    latency_ms: int
    token_count: int
    error: str | None = None


@dataclass
class Specialist:
    """Configuration for a single specialist model invocation."""

    model: str
    provider: str
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class BaseProvider(ABC):
    """
    Abstract base class that every LLM provider must implement.

    Subclasses are expected to handle authentication, request formatting,
    and response parsing specific to their provider API.
    """

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        Send a chat completion request and return the full response text.

        Args:
            model: Model identifier (e.g. ``"meta-llama/llama-3-70b"``).
            messages: Conversation history as a list of role/content dicts.
            system_prompt: Optional system-level instruction prepended to messages.
            temperature: Sampling temperature (0.0–2.0).
            max_tokens: Maximum number of tokens to generate.

        Returns:
            The assistant's reply as a plain string.

        Raises:
            ProviderError: On any provider-level failure.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion, yielding content tokens as they arrive.

        Args:
            model: Model identifier.
            messages: Conversation history.
            system_prompt: Optional system-level instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            Content token strings as they are received from the provider.

        Raises:
            ProviderError: On any provider-level failure.
        """
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """
        Return a list of available model identifiers from the provider.

        Raises:
            ProviderError: If the model list cannot be retrieved.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check whether the provider API is reachable and responding.

        Returns:
            True if the provider is healthy, False otherwise.
        """
        ...

    async def aclose(self) -> None:
        """
        Release any resources held by this provider (e.g. the shared
        ``httpx.AsyncClient``).  Called once during application shutdown.

        The default implementation is a no-op; subclasses that own a
        persistent client should override this.
        """
        return
