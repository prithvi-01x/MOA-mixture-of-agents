# MOA — Mixture of Agents

> A self-hosted AI orchestration system that runs multiple LLM specialists in parallel, then synthesises their outputs through a chairman model into a single, high-quality answer.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)

---

## Overview

MOA (Mixture of Agents) lets you configure multiple AI specialists — each from different providers (Groq and OpenRouter) or with different system prompts — and pits them against the same query simultaneously. A chairman model then reads all responses and synthesises the single best answer.

**Pipeline modes:**
| Mode | Description |
|------|-------------|
| `parallel` | All specialists run at the same time |
| `serial` | Each specialist sees the previous one's output |
| `debate` | Specialists run 2 rounds, arguing with each other's prior response |

---

## Architecture

```
Browser (React/Vite)
    │
    │  Server-Sent Events (SSE)
    ▼
FastAPI Backend
    ├── MoAPipeline  →  Specialist 1 (Groq)
    │                →  Specialist 2 (OpenRouter)
    │                →  Specialist N …
    │
    └── ChairmanAggregator  →  Chairman Model
                                    │
                            Final Answer (SSE stream)
```

**Tech stack:**

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 · TypeScript · Vite · Zustand · react-markdown |
| Backend | FastAPI · Uvicorn · Python 3.11+ |
| Database | SQLite via aiosqlite (persistent conversation history) |
| HTTP | httpx (connection pool + retry with exponential backoff) |
| Logging | loguru (JSON or human-readable, in-memory ring buffer) |
| Container | Docker Compose (backend + nginx frontend + optional Groq) |

---

## Features

- **Per-token streaming** — specialist tokens stream to the browser in real time via SSE
- **Three pipeline modes** — parallel, serial, debate
- **Conversation history** — all chats persisted in SQLite, resumable by ID
- **Markdown rendering** — code blocks with syntax highlighting (highlight.js github-dark)
- **System prompt editor** — per-specialist prompts with a localStorage template system
- **Dark / Light theme** — 🌙/☀️ toggle, persisted across sessions
- **Mobile-responsive** — hamburger sidebar overlay, single-column grid on small screens
- **Conversation export** — download as Markdown or JSON, copy to clipboard
- **Structured logging** — loguru JSON logs; `GET /api/logs` endpoint (when `DEBUG=true`)
- **Toast notifications** — real-time error feedback via react-hot-toast
- **Docker Compose** — production-ready with nginx reverse proxy and optional Groq service

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node 20+ and pnpm (`npm install -g pnpm`)
- [Groq](https://groq.ai) running locally (or an OpenRouter API key)

### 1. Clone & set up the backend

```bash
git clone <repo-url> && cd MOA

# Create virtualenv and install dependencies
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx aiosqlite loguru python-dotenv pydantic

# Copy and fill in your environment variables
cp .env.example .env
```

### 2. Start the backend

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev          # runs at http://localhost:5173
```

Open **http://localhost:5173** in your browser.

### 4. Or use the convenience script

```bash
chmod +x start.sh && ./start.sh
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the values:

```env
# ── Server ────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173

# ── Storage ───────────────────────────────────────────────
DB_PATH=~/.moa/moa.db
CONFIG_PATH=~/.moa/config.json

# ── Providers ─────────────────────────────────────────────
GROQ_API_KEY=http://localhost:11434

# ── Frontend ──────────────────────────────────────────────
VITE_API_URL=http://localhost:8000

# ── Logging ───────────────────────────────────────────────
LOG_FORMAT=        # "json" for structured output
LOG_LEVEL=INFO
DEBUG=false        # true → enables GET /api/logs

# ── Performance ───────────────────────────────────────────
HTTPX_MAX_CONNECTIONS=20
HTTPX_MAX_KEEPALIVE_CONNECTIONS=10
HTTPX_TIMEOUT=30.0

# ── Retry ─────────────────────────────────────────────────
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0

# ── Streaming ─────────────────────────────────────────────
SSE_QUEUE_SIZE=100
```

See `.env.example` for descriptions of every variable.

---

## Docker Deployment

### Standard deployment (backend + frontend)

```bash
docker compose up -d
```

- Frontend → `http://localhost` (port 80, nginx)
- Backend → `http://localhost:8000`

### With local Groq

```bash
docker compose --profile local up -d
```

This also starts the `groq/groq:latest` container on port 11434 with a named volume for models.

### Services

| Service | Image | Port |
|---------|-------|------|
| `backend` | `Dockerfile.backend` (python:3.12-slim + gunicorn) | 8000 |
| `frontend` | `Dockerfile.frontend` (node:20-slim build → nginx:alpine) | 80 |
| `groq` | `groq/groq:latest` (profile: `local`) | 11434 |

> The nginx config proxies `/api/*` to the backend and serves the React SPA with fallback routing.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Provider health status |
| `POST` | `/api/chat` | Run pipeline, stream SSE events |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get conversation with messages |
| `GET` | `/api/conversations/{id}/export?format=markdown\|json` | Export conversation |
| `GET` | `/api/models/groq` | List local Groq models |
| `GET` | `/api/keys` | List configured provider keys |
| `POST` | `/api/keys` | Set a provider API key |
| `GET` | `/api/logs?n=50` | Last N log lines (`DEBUG=true` only) |

### SSE Event Types

```jsonc
{"type": "conversation_id", "conversation_id": "..."}
{"type": "specialist_token", "model": "...", "provider": "...", "content": "tok"}
{"type": "specialist_done",  "model": "...", "provider": "...", "content": "...", "tokens_per_sec": 12.5, "latency_ms": 300, "error": null}
{"type": "chairman_start"}
{"type": "chairman_token", "content": "tok"}
{"type": "chairman_done"}
{"type": "error", "message": "..."}
```

---

## Development

### Backend

```bash
source venv/bin/activate

# Run with hot-reload
uvicorn main:app --reload

# Lint
pip install ruff
ruff check .

# Format
ruff format .
```

### Frontend

```bash
cd frontend

pnpm dev          # dev server at :5173 with /api proxy
pnpm build        # production bundle → dist/
pnpm lint         # eslint
pnpm vitest run   # unit + component tests
```

---

## Testing

### Backend — pytest

```bash
source venv/bin/activate
pytest tests/ -v --tb=short
```

**25 tests** covering:
- `test_chat.py` — happy path, one-fail, all-fail, serial mode, debate mode
- `test_conversations.py` — list, 404, appears-after-chat, multi-turn
- `test_export.py` — markdown headings, JSON Content-Disposition, 404
- `test_config.py` — config read/write/cache/invalidation
- `test_database.py` — table creation, message persistence, ratings

All tests use a temporary SQLite database (`tmp_path`) and a `FakeProvider` that returns deterministic tokens — **no real LLM calls needed**.

### Frontend — vitest

```bash
cd frontend && pnpm vitest run
```

**23 tests** covering:
- `SpecialistCard.test.tsx` — renders model name, streaming indicator, markdown, error badge
- `ChairmanPanel.test.tsx` — waiting state, streaming cursor, export menu, clipboard
- `SetupPage.test.tsx` — provider tabs, specialist picker, disabled start button

### CI

GitHub Actions workflows in `.github/workflows/`:
- `backend.yml` — ruff lint + pytest on every push/PR to `main`
- `frontend.yml` — pnpm lint + build + vitest on every push/PR to `main`

---

## Project Structure

```
MOA/
├── main.py                  # FastAPI app, CORS, lifespan
├── config.py                # Env var loading, config.json R/W
├── database.py              # aiosqlite schema + CRUD helpers
├── logger.py                # loguru setup, in-memory ring buffer
│
├── moa/
│   ├── pipeline.py          # MoAPipeline (parallel / serial / debate)
│   └── chairman.py          # ChairmanAggregator (synthesis via SSE)
│
├── providers/
│   ├── base.py              # BaseProvider ABC + SpecialistResult
│   ├── factory.py           # get_provider() + connection-pool cache
│   ├── groq.py            # Groq streaming provider
│   ├── openrouter.py        # OpenRouter streaming provider
│   └── retry.py             # Exponential backoff decorators
│
├── routers/
│   ├── chat.py              # POST /api/chat (SSE), GET /api/conversations
│   ├── export.py            # GET /api/conversations/{id}/export
│   ├── models.py            # GET /api/models/groq
│   ├── keys.py              # GET/POST /api/keys
│   ├── health.py            # GET /api/health
│   └── logs.py              # GET /api/logs (DEBUG only)
│
├── tests/
│   ├── conftest.py          # FakeProvider, async_client, patch fixtures
│   ├── test_chat.py         # /api/chat integration tests
│   ├── test_conversations.py
│   ├── test_export.py
│   ├── test_config.py
│   └── test_database.py
│
├── frontend/
│   ├── src/
│   │   ├── lib/api.ts       # SSE client, API helpers
│   │   ├── store/app.ts     # Zustand global store
│   │   ├── layouts/
│   │   │   └── AppLayout.tsx  # Sidebar, hamburger, theme toggle
│   │   ├── pages/
│   │   │   ├── SetupPage.tsx
│   │   │   └── ChatPage.tsx
│   │   └── components/
│   │       ├── chat/        # SpecialistCard, ChairmanPanel, ExportMenu, InputBar
│   │       └── setup/       # ProviderTabs, SpecialistPicker, ChairmanSelector …
│   └── nginx.conf           # /api proxy + SPA fallback
│
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── ruff.toml
└── .github/workflows/
    ├── backend.yml
    └── frontend.yml
```

---

## License

MIT
