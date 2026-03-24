"""
Logs router — exposes the in-memory log buffer (DEBUG mode only).

Enabled only when ``DEBUG=true`` is set in the environment.
"""

import os
from fastapi import APIRouter, HTTPException

from logger import log_buffer

router = APIRouter(tags=["logs"])

_DEBUG = os.getenv("DEBUG", "").strip().lower() in {"true", "1", "yes"}


@router.get("/logs")
async def get_logs(last: int = 100):
    """
    Return the last *last* log lines from the in-memory ring buffer.

    Only available when the server is started with ``DEBUG=true``.

    Args:
        last: Maximum number of recent log lines to return (max 200).
    """
    if not _DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Log endpoint is disabled. Set DEBUG=true to enable.",
        )
    lines = list(log_buffer)
    return {"lines": lines[-min(last, 200):]}
