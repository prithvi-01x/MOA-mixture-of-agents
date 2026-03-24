"""Tests for database.py — table creation, CRUD, and the JOIN query."""

import importlib
from uuid import uuid4

import pytest
import pytest_asyncio


@pytest.fixture(autouse=True)
def _reload_db(tmp_db_path):
    """Reload the database module so it picks up the temp DB_PATH."""
    import database
    importlib.reload(database)
    database.DB_PATH = tmp_db_path


@pytest_asyncio.fixture()
async def tables(tmp_db_path):
    """Create tables in the temp DB."""
    import database
    await database.create_tables()


@pytest.mark.asyncio
async def test_create_tables(tables):
    """Tables should be created without error."""
    import aiosqlite, database
    async with aiosqlite.connect(database.DB_PATH) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = {row[0] for row in await cursor.fetchall()}
    assert "conversations" in table_names
    assert "messages" in table_names
    assert "specialist_responses" in table_names
    assert "ratings" in table_names
    # model_configs should NOT exist (removed)
    assert "model_configs" not in table_names


@pytest.mark.asyncio
async def test_save_and_get_conversations(tables):
    """Saving a conversation should make it retrievable via get_conversations."""
    import database
    conv_id = str(uuid4())
    await database.save_conversation(conv_id, "Test title", "parallel")
    convs = await database.get_conversations()
    assert len(convs) >= 1
    found = [c for c in convs if c["id"] == conv_id]
    assert len(found) == 1
    assert found[0]["title"] == "Test title"


@pytest.mark.asyncio
async def test_save_message_updates_conversation(tables):
    """Saving a message should update the parent conversation's updated_at."""
    import database
    conv_id = str(uuid4())
    msg_id = str(uuid4())
    await database.save_conversation(conv_id, "Test", "parallel")
    conv_before = await database.get_conversation_by_id(conv_id)
    await database.save_message(msg_id, conv_id, "user", "Hello")
    conv_after = await database.get_conversation_by_id(conv_id)
    assert len(conv_after["messages"]) == 1
    assert conv_after["messages"][0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_get_conversation_by_id_with_specialists(tables):
    """get_conversation_by_id should return nested specialist_responses via JOIN."""
    import database
    conv_id = str(uuid4())
    msg_id = str(uuid4())
    sr_id = str(uuid4())

    await database.save_conversation(conv_id, "Test", "parallel")
    await database.save_message(msg_id, conv_id, "assistant", "Reply")
    await database.save_specialist_response(
        id=sr_id,
        message_id=msg_id,
        model="llama3",
        provider="ollama",
        content="Specialist reply",
        tokens_per_sec=12.5,
        latency_ms=300,
        token_count=50,
    )

    conv = await database.get_conversation_by_id(conv_id)
    assert conv is not None
    assert len(conv["messages"]) == 1
    msg = conv["messages"][0]
    assert len(msg["specialist_responses"]) == 1
    sr = msg["specialist_responses"][0]
    assert sr["model"] == "llama3"
    assert sr["content"] == "Specialist reply"
    assert sr["tokens_per_sec"] == 12.5


@pytest.mark.asyncio
async def test_get_conversation_by_id_returns_none(tables):
    """get_conversation_by_id returns None for non-existent ID."""
    import database
    result = await database.get_conversation_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_rate_response(tables):
    """rate_response should insert a rating row."""
    import aiosqlite, database
    conv_id = str(uuid4())
    msg_id = str(uuid4())
    rating_id = str(uuid4())

    await database.save_conversation(conv_id, "Test", "parallel")
    await database.save_message(msg_id, conv_id, "assistant", "Reply")
    await database.rate_response(rating_id, msg_id, 5)

    async with aiosqlite.connect(database.DB_PATH) as db:
        cursor = await db.execute("SELECT rating FROM ratings WHERE id = ?", (rating_id,))
        row = await cursor.fetchone()
    assert row is not None
    assert row[0] == 5
