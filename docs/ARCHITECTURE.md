# Architecture
## MoA — Mixture of Agents App

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** March 2026

---

## 1. Overview

MoA follows a local-first client-server architecture. The frontend is a Vite/React SPA communicating with a FastAPI backend over HTTP and SSE. The backend manages the MoA pipeline, abstracts provider differences, and persists data to SQLite.

```
Browser (localhost:5173)
        │
        │  HTTP REST + SSE
        ▼
FastAPI Backend (localhost:8000)
        │
        ├──► Ollama         (localhost:11434)
        ├──► OpenRouter     (api.openrouter.ai)
        ├──► Bytez          (api.bytez.com)
        └──► SQLite         (~/.moa/moa.db)
```

---

## 2. Component Architecture

### 2.1 Provider Layer

The provider layer is the foundation of the entire system. Every AI call goes through it.

```
BaseProvider (ABC)
    │
    ├── OllamaProvider
    │     ├── stream()      → chunked HTTP POST /api/chat
    │     ├── chat()        → non-streaming POST /api/chat
    │     └── list_models() → GET /api/tags
    │
    ├── OpenRouterProvider
    │     ├── stream()      → SSE POST /v1/chat/completions
    │     ├── chat()        → non-streaming POST /v1/chat/completions
    │     └── list_models() → returns [] (user provides model names)
    │
    └── BytezProvider
          ├── stream()      → polling GET /v1/models/{id}/run
          ├── chat()        → POST /v1/models/{id}/run
          └── list_models() → returns [] (user provides model names)
```

**Provider Factory:**
```python
def get_provider(provider_name: str) -> BaseProvider:
    return {
        "ollama":      OllamaProvider(),
        "openrouter":  OpenRouterProvider(api_key=get_key("openrouter")),
        "bytez":       BytezProvider(api_key=get_key("bytez")),
    }[provider_name]
```

---

### 2.2 MoA Pipeline Layer

```
MoAPipeline
    │
    ├── run_parallel(query, specialists, chairman)
    │     ├── asyncio.gather(specialist_tasks)   ← fires all at once
    │     └── chairman_aggregate(results)
    │
    ├── run_serial(query, specialists, chairman)
    │     ├── for each specialist: query with previous context
    │     └── chairman_aggregate(results)
    │
    └── run_debate(query, specialists, chairman)
          ├── round_1: initial answers
          ├── round_2: each specialist critiques others
          └── chairman_aggregate(critiques)
```

**Specialist Model:**
```python
@dataclass
class Specialist:
    model: str
    provider: str          # 'ollama' | 'openrouter' | 'bytez'
    system_prompt: str
    temperature: float
    max_tokens: int
```

**Chairman Model:**
```python
@dataclass
class Chairman:
    model: str
    provider: str
    aggregation_mode: str  # 'best' | 'combine' | 'best_and_combine'
```

---

### 2.3 Streaming Layer

The backend acts as a **streaming proxy** — it aggregates all specialist SSE streams into a single SSE stream for the frontend.

```
Frontend
  │
  │  EventSource('/api/chat')
  ▼
FastAPI SSE Generator
  │
  ├── asyncio.Queue per specialist
  │
  ├── Task 1: OllamaProvider.stream()     → queue_1.put(chunk)
  ├── Task 2: OpenRouterProvider.stream() → queue_2.put(chunk)
  └── Task 3: BytezProvider.stream()      → queue_3.put(chunk)
        │
        └── Merge all queues → yield SSE events to frontend
```

**SSE Event Types:**

| Event | Payload | When |
|---|---|---|
| `specialist_token` | `{id, model, provider, content, tok_s}` | Each token from specialist |
| `specialist_done` | `{id, model, total_tokens, latency_ms}` | Specialist finishes |
| `chairman_start` | `{}` | Chairman begins aggregating |
| `chairman_token` | `{content}` | Each token from chairman |
| `chairman_done` | `{total_tokens, latency_ms}` | Chairman finishes |
| `error` | `{id, message}` | Any provider error |

---

### 2.4 Data Layer

```
SQLite (~/.moa/moa.db)
    │
    ├── conversations      — session metadata
    ├── messages           — user + chairman messages
    ├── specialist_responses — per-model outputs + stats
    ├── model_configs      — saved specialist/chairman setups
    ├── ratings            — user ratings per chairman response
    └── api_keys           — encrypted provider keys
```

**Access Pattern:**
- All DB access goes through `database.py` — no raw SQL in routers
- Async reads with `aiosqlite`
- Writes on: conversation start, each specialist completion, chairman completion

---

### 2.5 Frontend State Architecture

```
App State (Zustand or React Context)
    │
    ├── setupState
    │     ├── specialists: Specialist[]
    │     ├── chairman: Chairman
    │     ├── pipelineMode: 'parallel' | 'serial' | 'debate'
    │     └── ollamaModels: string[]   ← fetched on load
    │
    └── chatState
          ├── conversations: Conversation[]
          ├── activeConversation: Conversation | null
          ├── specialistStreams: Record<string, StreamState>
          │     └── { content, isStreaming, tokPerSec, latencyMs }
          └── chairmanState: { content, isStreaming, isDone }
```

---

## 3. Data Flow — Full Query Lifecycle

```
1. User types query → InputBar → POST /api/chat
                                        │
2. FastAPI creates conversation + message in SQLite
                                        │
3. MoAPipeline.run_parallel() fires
   │
   ├── Task A: OllamaProvider.stream(dolphin3:8b, query)
   ├── Task B: OllamaProvider.stream(qwen2.5-coder:7b, query)
   └── Task C: OpenRouterProvider.stream(deepseek/r1, query)
                                        │
4. Each task yields tokens → merged SSE stream
                                        │
5. Frontend SpecialistCards receive tokens → render streaming text
                                        │
6. All specialists complete → stats saved to SQLite
                                        │
7. Chairman receives all outputs → generates final answer
                                        │
8. ChairmanPanel streams final answer
                                        │
9. Chairman response saved to SQLite → conversation updated
```

---

## 4. Error Handling Strategy

| Error Type | Handling |
|---|---|
| Ollama not running | Health check on startup, show warning banner |
| Model not found (Ollama) | Show error badge on specialist card, skip in pipeline |
| Invalid API key | Show error on setup screen, disable provider |
| OpenRouter rate limit (429) | Show rate limit badge, retry after delay |
| Bytez cold start timeout | Show "warming up" state, poll with backoff |
| Partial specialist failure | Continue with remaining specialists, note failure to chairman |
| Chairman failure | Show raw specialist responses, no aggregation |
| SQLite write failure | Log error, continue without persistence |

---

## 5. Security Considerations

- API keys stored in `~/.moa/config.json` with `600` permissions
- Keys never logged, never sent to frontend
- No authentication needed (local only)
- CORS restricted to `localhost:5173`
- No external analytics or telemetry

---

## 6. Performance Considerations

| Concern | Mitigation |
|---|---|
| Ollama VRAM (6GB) | `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0` |
| Slow Bytez cold start | Show loading state, non-blocking |
| Large chairman prompt | Truncate specialist responses to 1024 tokens each before sending to chairman |
| SQLite concurrent writes | Single writer pattern, async reads |
| Frontend rerender on stream | Virtualize specialist cards, throttle state updates to 60fps |

---

## 7. Deployment

```bash
# Start backend
cd moa/backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000

# Start frontend
cd moa/frontend
pnpm dev --host 127.0.0.1 --port 5173

# Access
open http://localhost:5173
```

Optional: create a single shell script `start.sh` that launches both with one command.

---

## 8. Future Architecture Extensions (Post-MVP)

| Extension | Approach |
|---|---|
| Debate mode | Add `run_debate()` to MoAPipeline |
| Per-model system prompts | Add `system_prompt` field to Specialist, pass to provider |
| Model performance dashboard | Aggregate `specialist_responses` table, expose `/api/stats` |
| Export | Read conversation from SQLite, serialize to MD/JSON |
| Response rating | POST `/api/ratings`, store in `ratings` table |
| Plugin providers | Extend BaseProvider ABC, register in factory |
