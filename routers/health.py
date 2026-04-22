"""Health-check router — reports live/down status for every provider."""

import asyncio

from fastapi import APIRouter

from providers.factory import get_provider

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Return reachability status for Groq and OpenRouter."""

    async def _check(provider_name: str) -> bool:
        try:
            provider = get_provider(provider_name)
            return await provider.health_check()
        except Exception:
            return False

    groq, openrouter = await asyncio.gather(
        _check("groq"),
        _check("openrouter"),
        return_exceptions=True,
    )

    return {
        "groq": groq if isinstance(groq, bool) else False,
        "openrouter": openrouter if isinstance(openrouter, bool) else False,
    }
