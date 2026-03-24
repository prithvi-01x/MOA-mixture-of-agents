# MOA — Lower Priority Improvements Prompt

You are working inside the MOA (Mixture of Agents) codebase — a FastAPI
backend + Vite/React/TypeScript frontend. The high-priority items
(per-token streaming, conversation history, serial/debate pipeline modes,
httpx connection pooling, retry with backoff) and medium-priority items
(markdown rendering, specialist system prompt editor, structured logging,
conversation export) are already implemented.

Implement the following lower-priority improvements in order. Complete
each one fully before moving to the next.

---

## 9. Integration Tests

**Backend — `tests/` directory:**
- Use FastAPI's `AsyncClient` with `pytest-asyncio` to test `/api/chat`
  end-to-end.
- Mock `providers.factory.get_provider` to return a fake provider that
  yields deterministic token chunks.
- Test cases to cover:
  - Happy path: 2 specialists + chairman, SSE events arrive in order
    (`specialist_done` × 2 → `chairman_start` → `chairman_token` × N
    → `chairman_done`).
  - One specialist fails: failed specialist has error set, chairman
    still runs with remaining results.
  - All specialists fail: stream yields "All specialist models failed
    to respond."
  - Serial mode: specialists run in sequence, each receives prior
    output as context.
  - Debate mode: two rounds of specialist invocations occur.
- Create `tests/test_conversations.py`:
  - `GET /api/conversations` returns empty list on fresh DB.
  - `GET /api/conversations/{id}` returns 404 for unknown ID.
  - After a `/api/chat` call, conversation appears in listing.
  - Multi-turn: two messages with same `conversation_id` both appear
    in `GET /api/conversations/{id}`.
- Create `tests/test_export.py`:
  - Markdown export contains expected headings and specialist names.
  - JSON export has correct `Content-Disposition` header.
- Patch `DB_PATH` to a `tmp_path` fixture so tests never touch
  `~/.moa/moa.db`.

---

## 10. Docker Compose

**Root of the project:**
- Create `docker-compose.yml` with three services:
  - `backend`: build from `Dockerfile.backend`, base image
    `python:3.12-slim`, run with `gunicorn main:app -w 2 -k
    uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`, mount
    `~/.moa` as a volume, pass `CORS_ORIGINS`, `DB_PATH`,
    `CONFIG_PATH`, `OLLAMA_BASE_URL` as env vars.
  - `frontend`: two-stage build — `node:20-slim` for
    `pnpm install && pnpm build`, then `nginx:alpine` to serve
    `dist/`. Include a custom `nginx.conf` that proxies `/api`
    to the backend service.
  - `ollama`: image `ollama/ollama:latest`, port 11434, named
    volume for models, gated behind a `--profile local` compose
    profile so it only starts when explicitly requested.
- Create `Dockerfile.backend`, `Dockerfile.frontend`,
  `frontend/nginx.conf`.
- Add `.dockerignore` excluding `__pycache__`, `.venv`,
  `node_modules`, `*.pyc`, `.env`.

---

## 11. `.env.example`

**Root of the project:**
- Create `.env.example` with every configurable variable, grouped
  and commented:

```env
# ── Server ──────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173

# ── Storage ─────────────────────────────────────────────
DB_PATH=~/.moa/moa.db
CONFIG_PATH=~/.moa/config.json

# ── Providers ───────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434

# ── Frontend ────────────────────────────────────────────
VITE_API_URL=http://localhost:8000

# ── Logging ─────────────────────────────────────────────
LOG_FORMAT=        # "json" for structured output
DEBUG=false        # enables GET /api/logs

# ── Performance ─────────────────────────────────────────
HTTPX_MAX_CONNECTIONS=20
HTTPX_MAX_KEEPALIVE_CONNECTIONS=10
HTTPX_TIMEOUT=30.0

# ── Retry ───────────────────────────────────────────────
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0

# ── Streaming ───────────────────────────────────────────
SSE_QUEUE_SIZE=100
```

- Update `config.py` to read all new env vars with sensible defaults.
- Add a "Configuration" section to `README.md` pointing to
  `.env.example`.

---

## 12. Responsive / Mobile Layout

**Frontend — `src/layouts/AppLayout.tsx`, `src/App.css`:**
- Add a hamburger (☰) button visible only below `768px`.
- Conversation sidebar: hidden by default on mobile, slides in as
  an overlay on hamburger tap, closes on outside tap or conversation
  select, always visible on desktop.
- Setup page: two-column specialist/chairman layout stacks to single
  column below `768px`.
- Chat view: specialist card grid becomes full-width single column
  below `768px`.
- Test at 375px (iPhone SE), 768px (iPad), 1280px (desktop).

---

## 13. Dark / Light Theme Toggle

**Frontend — `src/index.css`, `src/store/app.ts`,
`src/layouts/AppLayout.tsx`:**
- Add `:root[data-theme="light"]` block overriding every existing
  CSS custom property with light-mode values.
- Add `theme: 'dark' | 'light'` to the Zustand store with a
  `toggleTheme()` action that sets `data-theme` on
  `document.documentElement` and persists to
  `localStorage` under `moa:theme`.
- On app load in `src/main.tsx`, read `localStorage` and apply
  theme before first render to prevent flash.
- Add a 🌙 / ☀️ toggle button to the `AppLayout` header.
- Swap the highlight.js stylesheet between `github-dark` and
  `github` based on active theme.

---

## 14. CI Pipeline

**`.github/workflows/`:**
- Create `backend.yml`:
  - Trigger: push and PRs to `main`.
  - Steps: checkout → Python 3.12 → install deps → `ruff check .`
    → `pytest tests/ -v --tb=short`.
- Create `frontend.yml`:
  - Trigger: push and PRs to `main`.
  - Steps: checkout → Node 20 + pnpm → `pnpm install
    --frozen-lockfile` → `pnpm lint` → `pnpm build` →
    `pnpm vitest run`.
- Add `ruff.toml` at the project root: line length 88,
  select E/W/F rules.

---

## 15. Frontend Component Tests

**Frontend — `src/__tests__/`:**
- Install `@testing-library/react`, `@testing-library/user-event`,
  `jsdom` as dev dependencies. Configure vitest to use `jsdom`
  environment in `vite.config.ts`.
- `SpecialistCard.test.tsx`:
  - Renders model name and provider.
  - Shows streaming indicator when `isStreaming: true`.
  - Renders markdown content (not raw text).
  - Shows error badge when `error` is set.
- `SetupPage.test.tsx`:
  - Renders provider tabs (Ollama, OpenRouter, Bytez).
  - Selecting a specialist adds it to the store.
  - Removing a specialist removes it from the store.
  - System prompt textarea appears on chevron expand.
  - Saving a template stores it in `localStorage`.
- `ChairmanPanel.test.tsx`:
  - Shows "Waiting for specialists..." before chairman starts.
  - Shows streaming cursor when `isStreaming`.
  - Export menu appears on button click.
  - Copy button calls `navigator.clipboard.writeText`.
- Mock `lib/api.ts` via `vi.mock` — no real HTTP calls in tests.

---

## 16. WebSocket Migration

> ⚠️ Only implement if SSE causes real cancellation or reconnection
> issues in practice — this is a significant refactor.

**Backend:**
- Add a `WebSocket` endpoint at `/api/chat/ws` alongside the
  existing SSE endpoint (keep SSE for backward compatibility).
- Accept `ChatRequest` as the first JSON message from the client.
- Send the same event types as SSE as JSON frames.
- Handle client `{"type": "cancel"}` message by calling
  `asyncio.Task.cancel()` on the running pipeline tasks.
- Close the connection cleanly after `chairman_done`.

**Frontend — `src/lib/api.ts`:**
- Replace `EventSource` with `WebSocket` for the chat endpoint.
- Add auto-reconnect on unexpected close.

---

## 17. Rate Limiting & Auth

> ⚠️ Only implement if deploying beyond localhost.

**Backend — `main.py` and `middleware/auth.py`:**
- Install `slowapi`. Apply a `"20/minute"` per-IP rate limit to
  `POST /api/chat`.
- Add optional `API_KEY` env var. If set, add `X-API-Key` header
  middleware returning `401` for invalid keys. Exempt
  `GET /api/health`.
- Document in `.env.example` and `README.md`.

---

## 18. Streaming Backpressure

> ⚠️ Only implement if clients report dropped tokens in production.

**Backend — `routers/chat.py`:**
- Replace direct `yield` in the SSE generator with an
  `asyncio.Queue(maxsize=SSE_QUEUE_SIZE)`.
- Producer puts SSE strings into the queue; consumer reads from it.
- If the queue is full, the producer blocks — naturally throttling
  the upstream provider stream.

---

## 19. Production ASGI Server

> ⚠️ Do this last, only when ready to deploy.

**Root of the project:**
- Install `gunicorn`. Create `gunicorn.conf.py`:

```python
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
```

- Update `Dockerfile.backend` CMD to use `gunicorn` with this config.
- Move `uvicorn.run()` in `main.py` inside `if __name__ == "__main__"`
  (dev-only).
- Create `start.sh` for local dev:

```bash
#!/bin/bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
cd frontend && pnpm dev --host 127.0.0.1 --port 5173
```

---

## General Rules

- Do not break existing functionality — run existing tests after
  each change.
- Keep all type hints and docstrings consistent with the existing
  codebase style.
- Do not introduce new dependencies without checking
  `pyproject.toml` / `package.json` first.
- Items 16–19 are conditional — only implement if the note
  condition is met.
- After completing all items, summarize every file changed or created.
