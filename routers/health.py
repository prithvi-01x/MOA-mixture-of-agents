"""Health-check router — reports live/down status for every provider."""

import asyncio

from fastapi import APIRouter

from providers.factory import get_provider

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Return reachability status for Ollama, OpenRouter, and Bytez."""

    async def _check(provider_name: str) -> bool:
        try:
            provider = get_provider(provider_name)
            return await provider.health_check()
        except Exception:
            return False

    ollama, openrouter, bytez = await asyncio.gather(
        _check("ollama"),
        _check("openrouter"),
        _check("bytez"),
        return_exceptions=True,
    )

    return {
        "ollama": ollama if isinstance(ollama, bool) else False,
        "openrouter": openrouter if isinstance(openrouter, bool) else False,
        "bytez": bytez if isinstance(bytez, bool) else False,
    }
