"""Models router — lists available models from providers."""

from fastapi import APIRouter

from providers.factory import get_provider

router = APIRouter(tags=["models"])


@router.get("/groq/models")
async def list_groq_models():
    """Return the list of available Groq models."""
    try:
        provider = get_provider("groq")
        models = await provider.list_models()
        return {"models": models}
    except Exception:
        return {"models": [], "error": "Groq not reachable"}


@router.get("/openrouter/models")
async def list_openrouter_models():
    """Return the list of free OpenRouter models."""
    try:
        provider = get_provider("openrouter")
        models = await provider.list_models()
        return {"models": models}
    except Exception:
        return {"models": [], "error": "OpenRouter not reachable"}
