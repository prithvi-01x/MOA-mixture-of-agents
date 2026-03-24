"""
Integration tests for conversation list/get endpoints.
"""

import json

import pytest


_BASE_REQUEST = {
    "query": "What is 2+2?",
    "specialists": [
        {"model": "fake-a", "provider": "fake", "system_prompt": "Be helpful."},
    ],
    "chairman": {"model": "fake-chair", "provider": "fake"},
    "pipeline_mode": "parallel",
}


@pytest.mark.asyncio
async def test_get_conversations_empty(db, async_client):
    """GET /api/conversations returns an empty list on a fresh DB."""
    resp = await async_client.get("/api/conversations")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_conversation_not_found(db, async_client):
    """GET /api/conversations/{id} returns 404 for an unknown ID."""
    resp = await async_client.get("/api/conversations/nonexistent-id-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_conversation_appears_after_chat(db, async_client, fake_provider_factory):
    """After POST /api/chat, the conversation appears in GET /api/conversations."""
    chat_resp = await async_client.post("/api/chat", json=_BASE_REQUEST)
    assert chat_resp.status_code == 200

    convs = await async_client.get("/api/conversations")
    assert convs.status_code == 200
    data = convs.json()
    assert len(data) == 1
    assert data[0]["title"].startswith("What is 2+2?")


@pytest.mark.asyncio
async def test_multi_turn_messages(db, async_client, fake_provider_factory):
    """Two messages with the same conversation_id both appear under that conversation."""
    # First turn — creates the conversation
    chat1 = await async_client.post("/api/chat", json=_BASE_REQUEST)
    assert chat1.status_code == 200

    # Extract conversation_id from SSE
    events = [
        json.loads(line[len("data: "):])
        for line in chat1.content.decode().splitlines()
        if line.startswith("data: ")
    ]
    conv_id_events = [e for e in events if e.get("type") == "conversation_id"]
    assert conv_id_events, "conversation_id event missing from SSE stream"
    conv_id = conv_id_events[0]["conversation_id"]

    # Second turn — uses the same conversation_id
    req2 = {**_BASE_REQUEST, "query": "And 3+3?", "conversation_id": conv_id}
    chat2 = await async_client.post("/api/chat", json=req2)
    assert chat2.status_code == 200

    # Fetch the conversation and verify both user messages are present
    detail = await async_client.get(f"/api/conversations/{conv_id}")
    assert detail.status_code == 200
    conv_data = detail.json()
    user_messages = [m for m in conv_data.get("messages", []) if m["role"] == "user"]
    assert len(user_messages) == 2
