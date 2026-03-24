"""
Integration tests for POST /api/chat SSE endpoint.

Uses FastAPI's AsyncClient + httpx and mocks the provider factory so no
real LLM calls are made.
"""

import importlib
import json
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest

from providers.base import BaseProvider, ProviderError, SpecialistResult  # noqa: F401


# ---------------------------------------------------------------------------
# Fake provider
# ---------------------------------------------------------------------------

class FakeProvider(BaseProvider):
    """Returns deterministic token chunks."""

    def __init__(self, tokens: list[str] | None = None, fail: bool = False):
        self._tokens = tokens or ["Hello", " world", "!"]
        self._fail = fail

    async def stream(self, model, messages, system_prompt=None, temperature=0.7,
                     max_tokens=1024) -> AsyncGenerator[str, None]:
        if self._fail:
            raise ProviderError(provider="fake", message="Intentional failure", status_code=500)
        for tok in self._tokens:
            yield tok

    async def chat(self, model, messages, system_prompt=None, temperature=0.7,
                   max_tokens=1024) -> str:
        if self._fail:
            raise ProviderError(provider="fake", message="Intentional failure", status_code=500)
        return "".join(self._tokens)

    async def list_models(self) -> list[str]:
        return ["fake-model"]

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_sse(raw: bytes) -> list[dict]:
    """Parse raw SSE bytes → list of event dicts."""
    events = []
    for line in raw.decode().splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[len("data: "):]))
            except json.JSONDecodeError:
                pass
    return events


_BASE_REQUEST = {
    "query": "What is 2+2?",
    "specialists": [
        {"model": "fake-a", "provider": "fake", "system_prompt": "You are helpful."},
        {"model": "fake-b", "provider": "fake", "system_prompt": "You are helpful."},
    ],
    "chairman": {"model": "fake-chair", "provider": "fake"},
    "pipeline_mode": "parallel",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_happy_path(db, async_client, fake_provider_factory):
    """Happy path: 2 specialists + chairman, events arrive in correct order."""
    resp = await async_client.post("/api/chat", json=_BASE_REQUEST)
    assert resp.status_code == 200

    events = _parse_sse(resp.content)
    types = [e["type"] for e in events]

    # Must have conversation_id first
    assert types[0] == "conversation_id"

    # Must have at least 2 specialist_done events
    done_events = [e for e in events if e["type"] == "specialist_done"]
    assert len(done_events) == 2

    # Chairman events after specialist_done
    done_idx = max(i for i, e in enumerate(events) if e["type"] == "specialist_done")
    remaining = [e["type"] for e in events[done_idx + 1:]]
    assert "chairman_start" in remaining
    assert "chairman_done" in remaining


@pytest.mark.asyncio
async def test_chat_one_specialist_fails(db, async_client, fake_provider_factory_one_fail):
    """Second stream call fails; chairman still runs."""
    resp = await async_client.post("/api/chat", json=_BASE_REQUEST)
    assert resp.status_code == 200

    events = _parse_sse(resp.content)
    done_events = [e for e in events if e["type"] == "specialist_done"]
    assert len(done_events) == 2

    errors = [e for e in done_events if e.get("error")]
    assert len(errors) >= 1  # at least one specialist failed

    # Chairman must still run
    types = [e["type"] for e in events]
    assert "chairman_start" in types
    assert "chairman_done" in types


@pytest.mark.asyncio
async def test_chat_all_specialists_fail(db, async_client, fake_provider_all_fail):
    """All specialists fail → chairman yields failure message."""
    resp = await async_client.post("/api/chat", json=_BASE_REQUEST)
    assert resp.status_code == 200

    events = _parse_sse(resp.content)
    chairman_tokens = [e["content"] for e in events if e["type"] == "chairman_token"]
    combined = "".join(chairman_tokens)
    assert "failed" in combined.lower()


@pytest.mark.asyncio
async def test_chat_serial_mode(db, async_client, fake_provider_factory):
    """Serial mode: pipeline runs without error, returns specialist_done events."""
    req = {**_BASE_REQUEST, "pipeline_mode": "serial"}
    resp = await async_client.post("/api/chat", json=req)
    assert resp.status_code == 200

    events = _parse_sse(resp.content)
    done_events = [e for e in events if e["type"] == "specialist_done"]
    assert len(done_events) == 2


@pytest.mark.asyncio
async def test_chat_debate_mode(db, async_client, fake_provider_factory):
    """Debate mode: runs 2 rounds internally but emits 1 specialist_done per specialist."""
    req = {**_BASE_REQUEST, "pipeline_mode": "debate"}
    resp = await async_client.post("/api/chat", json=req)
    assert resp.status_code == 200

    events = _parse_sse(resp.content)
    done_events = [e for e in events if e["type"] == "specialist_done"]
    # run_debate returns one SpecialistResult per specialist (final round result)
    # so specialist_done count == number of specialists == 2
    assert len(done_events) == 2

    types = [e["type"] for e in events]
    assert "chairman_start" in types
    assert "chairman_done" in types
