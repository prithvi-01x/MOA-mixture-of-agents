"""Models router — lists available models from providers."""

from fastapi import APIRouter

from providers.factory import get_provider

router = APIRouter(tags=["models"])


@router.get("/ollama/models")
async def list_ollama_models():
    """Return the list of locally-available Ollama models."""
    try:
        provider = get_provider("ollama")
        models = await provider.list_models()
        return {"models": models}
    except Exception:
        return {"models": [], "error": "Ollama not running"}
