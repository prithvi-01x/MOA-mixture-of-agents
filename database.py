"""
Async SQLite database layer for the MOA FastAPI application.

All raw SQL is confined to this module. Uses aiosqlite for async operations.
DB path is read from the DB_PATH environment variable (default: ~/.moa/moa.db).
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

DB_PATH = os.getenv("DB_PATH", str(Path.home() / ".moa" / "moa.db"))


def _ensure_db_dir() -> None:
    """Create the parent directory for the database file if it doesn't exist."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def _get_connection():
    """Async context manager: open a configured aiosqlite connection, yield it, then close."""
    _ensure_db_dir()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        yield conn


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

async def create_tables() -> None:
    """Create all application tables if they do not already exist."""
    _ensure_db_dir()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT,
                pipeline_mode TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id              TEXT PRIMARY KEY,
                conversation_id TEXT REFERENCES conversations(id),
                role            TEXT,
                content         TEXT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS specialist_responses (
                id             TEXT PRIMARY KEY,
                message_id     TEXT REFERENCES messages(id),
                model          TEXT,
                provider       TEXT,
                content        TEXT,
                tokens_per_sec REAL,
                latency_ms     INTEGER,
                token_count    INTEGER,
                created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


        await db.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id         TEXT PRIMARY KEY,
                message_id TEXT REFERENCES messages(id),
                rating     INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

async def save_conversation(id: str, title: str, pipeline_mode: str) -> None:
    """Insert or replace a conversation record."""
    async with _get_connection() as db:
        await db.execute(
            """
            INSERT INTO conversations (id, title, pipeline_mode)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title        = excluded.title,
                pipeline_mode = excluded.pipeline_mode,
                updated_at   = CURRENT_TIMESTAMP
            """,
            (id, title, pipeline_mode),
        )
        await db.commit()


async def get_conversations() -> list[dict]:
    """Return all conversations ordered by most recently updated first."""
    async with _get_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_conversation_by_id(id: str) -> dict | None:
    """
    Return a single conversation with its messages and specialist_responses
    nested under each message.  Returns None when the conversation doesn't exist.

    Uses a single LEFT JOIN query to avoid N+1 per-message lookups.
    """
    async with _get_connection() as db:
        # Fetch conversation
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE id = ?", (id,)
        )
        conv_row = await cursor.fetchone()
        if conv_row is None:
            return None

        conversation = dict(conv_row)

        # Single JOIN: messages + specialist_responses
        cursor = await db.execute(
            """
            SELECT
                m.id            AS m_id,
                m.conversation_id AS m_conversation_id,
                m.role          AS m_role,
                m.content       AS m_content,
                m.created_at    AS m_created_at,
                sr.id           AS sr_id,
                sr.model        AS sr_model,
                sr.provider     AS sr_provider,
                sr.content      AS sr_content,
                sr.tokens_per_sec AS sr_tokens_per_sec,
                sr.latency_ms   AS sr_latency_ms,
                sr.token_count  AS sr_token_count,
                sr.created_at   AS sr_created_at
            FROM messages m
            LEFT JOIN specialist_responses sr ON sr.message_id = m.id
            WHERE m.conversation_id = ?
            ORDER BY m.created_at ASC, sr.created_at ASC
            """,
            (id,),
        )
        rows = await cursor.fetchall()

        # Group into messages with nested specialist_responses
        messages: dict[str, dict] = {}  # keyed by message id, preserves order
        for row in rows:
            row_dict = dict(row)
            msg_id = row_dict["m_id"]
            if msg_id not in messages:
                messages[msg_id] = {
                    "id": row_dict["m_id"],
                    "conversation_id": row_dict["m_conversation_id"],
                    "role": row_dict["m_role"],
                    "content": row_dict["m_content"],
                    "created_at": row_dict["m_created_at"],
                    "specialist_responses": [],
                }
            # Attach specialist response if present (LEFT JOIN may produce NULLs)
            if row_dict["sr_id"] is not None:
                messages[msg_id]["specialist_responses"].append({
                    "id": row_dict["sr_id"],
                    "message_id": msg_id,
                    "model": row_dict["sr_model"],
                    "provider": row_dict["sr_provider"],
                    "content": row_dict["sr_content"],
                    "tokens_per_sec": row_dict["sr_tokens_per_sec"],
                    "latency_ms": row_dict["sr_latency_ms"],
                    "token_count": row_dict["sr_token_count"],
                    "created_at": row_dict["sr_created_at"],
                })

        conversation["messages"] = list(messages.values())
        return conversation


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

async def save_message(id: str, conversation_id: str, role: str, content: str) -> None:
    """Insert a new message and touch the parent conversation's updated_at."""
    async with _get_connection() as db:
        await db.execute(
            "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
            (id, conversation_id, role, content),
        )
        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Specialist responses
# ---------------------------------------------------------------------------

async def save_specialist_response(
    id: str,
    message_id: str,
    model: str,
    provider: str,
    content: str,
    tokens_per_sec: float,
    latency_ms: int,
    token_count: int,
) -> None:
    """Insert a specialist response linked to a message."""
    async with _get_connection() as db:
        await db.execute(
            """
            INSERT INTO specialist_responses
                (id, message_id, model, provider, content, tokens_per_sec, latency_ms, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (id, message_id, model, provider, content, tokens_per_sec, latency_ms, token_count),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------

async def rate_response(id: str, message_id: str, rating: int) -> None:
    """Insert a rating for a message."""
    async with _get_connection() as db:
        await db.execute(
            "INSERT INTO ratings (id, message_id, rating) VALUES (?, ?, ?)",
            (id, message_id, rating),
        )
        await db.commit()
