# MOA — Additional Improvements & Feature Ideas

## 🔧 Architecture & Backend

### 1. Implement Serial & Debate Pipeline Modes
The UI already shows "Serial Chain" and "Multi-Agent Debate" as POST-MVP options. The backend only implements `parallel`.
- **Serial**: Each specialist receives the previous specialist's output as context, building a chain of refinement.
- **Debate**: Specialists see each other's responses and critique/improve them over multiple rounds.
- Add `run_serial()` and `run_debate()` to `MoAPipeline`, dispatch based on `pipeline_mode` in the chat router.

### 2. Conversation History in Chat
Currently each `/api/chat` call creates a **new conversation** — there's no multi-turn. Users can't follow up.
- Accept an optional `conversation_id` in `ChatRequest`.
- Prepend prior messages from the DB to the specialist prompt.
- The frontend needs a conversation sidebar that loads past chats and resumes them.

### 3. WebSocket Instead of SSE
SSE is one-directional (server → client). Switching to WebSockets enables:
- Client-side cancellation mid-stream (currently the abort only drops the HTTP connection).
- Bi-directional events (e.g. user typing indicators, real-time config changes).
- Better resilience with auto-reconnection.

### 4. Rate Limiting & Auth
No authentication or rate limiting exists. For any deployment beyond localhost:
- Add API key auth or JWT middleware.
- Add rate limiting (e.g. `slowapi`) to prevent abuse of cloud provider credits.

### 5. Persistent Specialist Streaming (per-token SSE)
Currently specialists run to completion, then emit a single `specialist_done` event. The UI shows specialists as "streaming" but they're actually just waiting.
- Stream specialist tokens as `specialist_token` events in real-time.
- Show live typing in each `SpecialistCard` as tokens arrive.

---

## 🎨 Frontend & UX

### 6. Markdown Rendering
Both specialist and chairman outputs are plain text. Adding a markdown renderer (e.g. `react-markdown` + `rehype-highlight`) would:
- Properly format code blocks, lists, tables, and headings.
- Syntax-highlight code snippets.

### 7. Dark/Light Theme Toggle
The design system is locked to dark mode. Add a theme toggle:
- Define `:root[data-theme="light"]` CSS variables.
- Store preference in `localStorage`.

### 8. Responsive / Mobile Layout
The sidebar + two-column layout doesn't work on small screens.
- Collapse sidebar to a hamburger menu on mobile.
- Stack setup columns vertically.
- Full-width specialist cards.

### 9. Specialist System Prompt Editor
Users can't edit per-specialist system prompts from the UI — they're hardcoded to "You are a helpful assistant."
- Add an expandable textarea on each selected specialist card in the setup page.
- Allow saving prompt templates.

### 10. Conversation Export
Add a way to export conversations:
- Copy full conversation as Markdown.
- Download as JSON (including specialist responses and metrics).
- Share link (requires backend persistence endpoint).

---

## ⚡ Performance & Reliability

### 11. Connection Pooling for httpx
Every provider call creates a new `httpx.AsyncClient`. This means a new TCP+TLS handshake each time.
- Create a shared `httpx.AsyncClient` per provider (with connection pooling).
- Initialize in the provider constructor, close on app shutdown via `lifespan`.

### 12. Streaming Backpressure
If the chairman model produces tokens faster than the client reads them, the SSE buffer grows unbounded.
- Add a bounded async queue between the aggregator and the SSE generator.
- Drop older tokens or apply backpressure if the client falls behind.

### 13. Retry with Exponential Backoff
Provider calls can transiently fail (rate limits, timeouts). Currently failures are immediate.
- Add configurable retry logic (e.g. 3 attempts with exponential backoff) in `BaseProvider` or the pipeline.

### 14. Structured Logging
All logging is print-based or `console.error`. Add structured logging:
- Backend: Use `structlog` or `loguru` with JSON output.
- Frontend: Replace `console.error` with a toast notification system.

---

## 🧪 Testing & CI

### 15. Integration Tests
The current tests cover units (config, DB, store). Add:
- `pytest` tests that hit the FastAPI endpoints via `httpx.AsyncClient` (TestClient).
- Mock the provider layer to test the full chat pipeline end-to-end.

### 16. Frontend Component Tests
Add `@testing-library/react` + `vitest` tests for:
- `SetupPage` — specialist selection flow.
- `ChatPage` — rendering of specialist cards and chairman panel.
- `SpecialistCard` — error state rendering.

### 17. CI Pipeline
Set up GitHub Actions (or equivalent):
- Run `pytest` on push.
- Run `pnpm lint && pnpm build && pnpm vitest run` on push.
- Fail on lint errors or test failures.

---

## 📦 Deployment

### 18. Docker Compose
Create a `docker-compose.yml` with:
- `backend` service (FastAPI + uvicorn).
- `frontend` service (nginx serving the Vite build).
- Optional `ollama` service for local model inference.

### 19. Environment Configuration
Create a `.env.example` with all configurable variables:
```
CORS_ORIGINS=http://localhost:5173
DB_PATH=~/.moa/moa.db
CONFIG_PATH=~/.moa/config.json
OLLAMA_BASE_URL=http://localhost:11434
VITE_API_URL=http://localhost:8000
```

### 20. Production ASGI Server
Replace `uvicorn.run()` dev mode with a production-ready setup:
- Use `gunicorn` with `uvicorn.workers.UvicornWorker`.
- Configure `--workers` based on CPU cores.
