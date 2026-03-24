"""
Integration tests for GET /api/conversations/{id}/export.
"""

import json

import pytest


_BASE_REQUEST = {
    "query": "Explain gravity.",
    "specialists": [
        {"model": "newton", "provider": "fake", "system_prompt": "Be helpful."},
    ],
    "chairman": {"model": "fake-chair", "provider": "fake"},
    "pipeline_mode": "parallel",
}


async def _run_chat_and_get_conv_id(client) -> str:
    """Helper: run a chat and return the conversation_id."""
    resp = await client.post("/api/chat", json=_BASE_REQUEST)
    assert resp.status_code == 200
    events = [
        json.loads(line[len("data: "):])
        for line in resp.content.decode().splitlines()
        if line.startswith("data: ")
    ]
    conv_id_events = [e for e in events if e.get("type") == "conversation_id"]
    return conv_id_events[0]["conversation_id"]


@pytest.mark.asyncio
async def test_export_markdown_contains_query(db, async_client, fake_provider_factory):
    """Markdown export contains the original query and specialist model name."""
    conv_id = await _run_chat_and_get_conv_id(async_client)

    resp = await async_client.get(
        f"/api/conversations/{conv_id}/export", params={"format": "markdown"}
    )
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]

    body = resp.text
    # Query should appear somewhere in the markdown
    assert "gravity" in body.lower() or "Explain" in body
    # Specialist model name should appear as a heading
    assert "newton" in body.lower()


@pytest.mark.asyncio
async def test_export_json_content_disposition(db, async_client, fake_provider_factory):
    """JSON export has Content-Disposition: attachment header."""
    conv_id = await _run_chat_and_get_conv_id(async_client)

    resp = await async_client.get(
        f"/api/conversations/{conv_id}/export", params={"format": "json"}
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    assert "attachment" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_export_unknown_conversation(db, async_client):
    """Export returns 404 for an unknown conversation ID."""
    resp = await async_client.get(
        "/api/conversations/no-such-id/export", params={"format": "markdown"}
    )
    assert resp.status_code == 404
