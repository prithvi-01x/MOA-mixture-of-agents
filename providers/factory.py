"""
Provider factory — returns the correct ``BaseProvider`` subclass for a given
provider name, with API keys resolved from the application config.

Provider instances are cached at module level so the shared ``httpx.AsyncClient``
inside each provider is reused across requests (connection pooling).
"""

from config import get_key
from providers.base import BaseProvider
from providers.ollama import OllamaProvider
from providers.openrouter import OpenRouterProvider
from providers.bytez import BytezProvider

# Module-level cache keyed by provider name.
# Referenced by main.py lifespan to close clients on shutdown.
_provider_cache: dict[str, BaseProvider] = {}


def get_provider(provider_name: str) -> BaseProvider:
    """
    Return a cached ``BaseProvider`` instance matching *provider_name*.

    The first call for each provider creates and caches the instance.
    Subsequent calls return the same instance, allowing the shared
    ``httpx.AsyncClient`` inside each provider to pool connections.

    Args:
        provider_name: One of ``"ollama"``, ``"openrouter"``, or ``"bytez"``.

    Returns:
        A ready-to-use ``BaseProvider`` instance.

    Raises:
        ValueError: If *provider_name* is not recognised.
    """
    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    if provider_name == "ollama":
        provider: BaseProvider = OllamaProvider()

    elif provider_name == "openrouter":
        key = get_key("openrouter")
        provider = OpenRouterProvider(api_key=key)

    elif provider_name == "bytez":
        key = get_key("bytez")
        provider = BytezProvider(api_key=key)

    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    _provider_cache[provider_name] = provider
    return provider
