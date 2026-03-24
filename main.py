"""MoA (Mixture of Agents) — FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables
from routers import chat, models, keys, health, logs, export

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    ).split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: runs startup / shutdown logic."""
    await create_tables()
    yield
    # Gracefully close shared httpx clients in all cached providers
    from providers.factory import _provider_cache  # type: ignore[attr-defined]
    for provider in _provider_cache.values():
        await provider.aclose()


app = FastAPI(
    title="MoA – Mixture of Agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(keys.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(export.router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
