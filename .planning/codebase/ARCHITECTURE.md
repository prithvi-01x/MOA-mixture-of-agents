# Architecture

**Analysis Date:** 2025-05-15

## Pattern Overview

**Overall:** Local-first Client-Server Architecture (React SPA + FastAPI Backend)

**Key Characteristics:**
- **Streaming Proxy:** The backend aggregates multiple concurrent specialist streams into a single SSE stream for the frontend.
- **Provider Abstraction:** A common interface (`BaseProvider`) allows uniform interaction with diverse LLM backends (Ollama, OpenRouter, Bytez).
- **Plug-and-Play Pipelines:** Different MoA strategies (Parallel, Serial, Debate) are implemented as methods within the `MoAPipeline` class.

## Layers

**Frontend (UI):**
- Purpose: Provides the user interface for configuring specialists, managing conversations, and viewing real-time streaming results.
- Location: `frontend/src/`
- Contains: React components, Zustand state store, and API client.
- Depends on: FastAPI Backend (via HTTP/SSE).
- Used by: End user.

**API Layer (FastAPI):**
- Purpose: Exposes REST and SSE endpoints for frontend interaction, handles persistence, and orchestrates the MoA pipeline.
- Location: `routers/`
- Contains: Chat, model list, API key management, and export endpoints.
- Depends on: `moa/` (Pipeline), `providers/` (LLM clients), `database.py` (SQLite).
- Used by: Frontend.

**Orchestration Layer (MoA Pipeline):**
- Purpose: Manages the execution flow of multiple specialist models according to the selected mode (Parallel, Serial, Debate).
- Location: `moa/pipeline.py`
- Contains: `MoAPipeline` class with methods for different MoA strategies.
- Depends on: `providers/` (LLM clients).
- Used by: `routers/chat.py`.

**Provider Layer:**
- Purpose: Provides a uniform interface for interacting with various LLM service providers.
- Location: `providers/`
- Contains: `BaseProvider` ABC and concrete implementations for `Ollama`, `OpenRouter`, and `Bytez`.
- Depends on: `httpx` for async HTTP requests.
- Used by: `moa/pipeline.py`.

**Data Layer (Persistence):**
- Purpose: Persists conversations, messages, specialist responses, and configuration to a local SQLite database.
- Location: `database.py`
- Contains: `aiosqlite` wrappers for DB operations.
- Depends on: `sqlite3` via `aiosqlite`.
- Used by: `routers/` (Chat, Logs, Export).

## Data Flow

**User Query Lifecycle:**

1. **Input:** User submits a query via the `InputBar` in `frontend/src/pages/ChatPage.tsx`.
2. **Request:** Frontend sends a POST request to `/api/chat` (handled in `routers/chat.py`).
3. **Initialization:** Backend creates a new conversation and user message in SQLite (`database.py`).
4. **Pipeline Execution:** `MoAPipeline.run_parallel` (or other mode) is invoked in `moa/pipeline.py`.
5. **Specialist Invocation:** Pipeline calls `provider.stream()` for each selected specialist in `providers/`.
6. **Token Streaming:** Specialist tokens are captured via a callback and funneled into an `asyncio.Queue` in `routers/chat.py`.
7. **SSE Emission:** The FastAPI SSE generator drains the queue and yields `specialist_token` events to the frontend.
8. **Frontend Rendering:** `ChatPage.tsx` receives events and updates the `zustand` store (`frontend/src/store/app.ts`), which triggers re-renders of `SpecialistCard.tsx`.
9. **Aggregation:** Once specialists finish, `ChairmanAggregator` in `moa/chairman.py` is invoked to produce the final response.
10. **Finalization:** Chairman tokens are streamed to the frontend (`chairman_token`), and the final assistant message + specialist stats are saved to SQLite.

**State Management:**
- **Frontend:** Managed by `zustand` in `frontend/src/store/app.ts`. Handles real-time streaming state, configuration, and conversation history.
- **Backend:** Primarily stateless per request, but persists state (conversations, messages) to SQLite via `database.py`.

## Key Abstractions

**`BaseProvider`:**
- Purpose: Abstract base class defining the interface for all LLM providers (streaming and non-streaming chat).
- Examples: `providers/base.py`, `providers/ollama.py`, `providers/openrouter.py`.
- Pattern: Adapter Pattern.

**`MoAPipeline`:**
- Purpose: Orchestrates the execution of multiple specialists.
- Examples: `moa/pipeline.py`.
- Pattern: Strategy Pattern (Parallel, Serial, Debate).

**`ChairmanAggregator`:**
- Purpose: Aggregates multiple specialist responses into a single, high-quality final answer.
- Examples: `moa/chairman.py`.
- Pattern: Aggregator / Reducer.

## Entry Points

**Backend Entry Point:**
- Location: `main.py`
- Triggers: `uvicorn main:app`.
- Responsibilities: Initializes FastAPI, configures CORS, mounts routers, and manages the application lifespan (database setup/cleanup).

**Frontend Entry Point:**
- Location: `frontend/src/main.tsx`
- Triggers: Browser loading the application.
- Responsibilities: Renders the React root component (`App.tsx`) and initializes global styles.

## Error Handling

**Strategy:** Multi-level error propagation and graceful degradation.

**Patterns:**
- **Provider Retries:** `providers/retry.py` implements exponential backoff for transient failures (e.g., rate limits).
- **Partial Failure:** If a specialist fails, its result contains an error message; the MoA pipeline continues with remaining specialists, and the chairman is notified of the failure.
- **SSE Error Events:** Backend catches exceptions during the streaming process and emits an `error` event to inform the frontend.

## Cross-Cutting Concerns

**Logging:** Structured logging using `logger.py` for both system events and pipeline stats.
**Validation:** Pydantic models in `routers/` for request/response validation.
**CORS:** Middleware in `main.py` allowing frontend access from specified origins.

---

*Architecture analysis: 2025-05-15*
