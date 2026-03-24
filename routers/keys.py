"""Keys router — manage provider API keys."""

from fastapi import APIRouter
from pydantic import BaseModel

from config import get_key, set_key

router = APIRouter(tags=["keys"])


class SetKeyRequest(BaseModel):
    provider: str
    key: str


@router.post("/keys")
async def save_key(body: SetKeyRequest):
    """Store an API key for the given provider."""
    set_key(body.provider, body.key)
    return {"success": True}


@router.get("/keys/{provider}")
async def retrieve_key(provider: str):
    """Return a masked version of the stored key (last 4 chars only)."""
    key = get_key(provider)
    masked = f"****{key[-4:]}" if key else None
    return {"provider": provider, "key": masked}
