# System Design
## MoA — Mixture of Agents App

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** March 2026

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│          Vite + React + TailwindCSS + shadcn/ui             │
│                    + Framer Motion                          │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP / WebSocket / SSE
┌─────────────────────▼───────────────────────────────────────┐
│                        BACKEND                              │
│                   FastAPI (Python, async)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  MoA Engine  │  │  Provider    │  │  History &       │  │
│  │  (pipeline)  │  │  Abstraction │  │  Stats Service   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────┬──────────────────┬───────────────────┬───────────────┘
       │                  │                   │
┌──────▼──────┐  ┌────────▼───────┐  ┌────────▼────────┐
│   Ollama    │  │  OpenRouter    │  │     Bytez       │
│  localhost  │  │  (cloud API)   │  │  (HF serverless)│
│  :11434     │  │                │  │                 │
└─────────────┘  └────────────────┘  └─────────────────┘
                          │
                 ┌────────▼────────┐
                 │     SQLite      │
                 │  (local DB)     │
                 └─────────────────┘
```

---

## 2. Provider Abstraction Layer

All three providers implement a single `BaseProvider` interface. This is the most critical design decision — everything else depends on it.

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseProvider(ABC):

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict],
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Non-streaming chat completion"""
        pass

    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict],
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion — yields token chunks"""
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models (Ollama only, others return empty)"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is reachable"""
        pass
```

### Provider Implementations

| Provider | Stream Method | Auth | Base URL |
|---|---|---|---|
| `OllamaProvider` | Chunked HTTP (`/api/chat`) | None | `localhost:11434` |
| `OpenRouterProvider` | SSE (`text/event-stream`) | Bearer token | `openrouter.ai/api/v1` |
| `BytezProvider` | Polling (no native stream) | API Key header | `api.bytez.com` |

---

## 3. MoA Pipeline Engine

```python
# moa/pipeline.py

class MoAPipeline:

    async def run_parallel(self, query, specialists, chairman):
        # Fire all specialists simultaneously
        tasks = [self.query_specialist(s, query) for s in specialists]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Chairman aggregates
        final = await self.chairman_aggregate(chairman, query, results)
        return final

    async def run_serial(self, query, specialists, chairman):
        # Each model receives previous model's output as context
        context = query
        results = []
        for specialist in specialists:
            result = await self.query_specialist(specialist, context)
            results.append(result)
            context = f"Previous answer: {result}\n\nImprove or build on this:"
        final = await self.chairman_aggregate(chairman, query, results)
        return final

    async def run_debate(self, query, specialists, chairman):
        # Round 1: initial answers
        round1 = await asyncio.gather(*[
            self.query_specialist(s, query) for s in specialists
        ])
        # Round 2: each model critiques all others
        critiques = await asyncio.gather(*[
            self.query_specialist(s, self.build_critique_prompt(query, round1))
            for s in specialists
        ])
        # Chairman decides
        final = await self.chairman_aggregate(chairman, query, critiques)
        return final
```

### VRAM Note
Despite `asyncio.gather()` firing simultaneously, Ollama processes one model at a time due to `OLLAMA_MAX_LOADED_MODELS=1`. The async wrapper makes the UI feel parallel even though execution is sequential.

---

## 4. Streaming Architecture

Frontend connects to backend via **Server-Sent Events (SSE)**. Backend fans out to each provider using their native streaming method, then re-emits tokens to the frontend per specialist.

```
Frontend ◄──── SSE stream ────── FastAPI
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
         Ollama chunks          OpenRouter SSE         Bytez polling
         (chunked HTTP)         (EventSource)          (interval GET)
```

### SSE Event Format
```json
{
  "type": "token",
  "specialist_id": "dolphin3:8b",
  "provider": "ollama",
  "content": "The attacker",
  "tok_per_sec": 38.4,
  "is_done": false
}

{
  "type": "chairman",
  "content": "Final aggregated answer...",
  "is_done": true
}
```

---

## 5. Database Schema (SQLite)

```sql
-- Conversations
CREATE TABLE conversations (
    id          TEXT PRIMARY KEY,
    title       TEXT,
    pipeline_mode TEXT,   -- 'parallel' | 'serial' | 'debate'
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id),
    role            TEXT,   -- 'user' | 'chairman'
    content         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Specialist Responses
CREATE TABLE specialist_responses (
    id              TEXT PRIMARY KEY,
    message_id      TEXT REFERENCES messages(id),
    model           TEXT,
    provider        TEXT,   -- 'ollama' | 'openrouter' | 'bytez'
    content         TEXT,
    tokens_per_sec  REAL,
    latency_ms      INTEGER,
    token_count     INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Model Configs (saved setups)
CREATE TABLE model_configs (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    specialists     TEXT,   -- JSON array
    chairman        TEXT,   -- JSON object
    pipeline_mode   TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Response Ratings
CREATE TABLE ratings (
    id              TEXT PRIMARY KEY,
    message_id      TEXT REFERENCES messages(id),
    rating          INTEGER,  -- 1-5
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API Keys (local, never transmitted elsewhere)
CREATE TABLE api_keys (
    provider        TEXT PRIMARY KEY,  -- 'openrouter' | 'bytez'
    key_value       TEXT,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Chairman Prompt Engineering

```
You are a Chairman AI. Your job is to produce the single best possible answer
by synthesizing responses from multiple specialist AI models.

Original Question:
{query}

Specialist Responses:
{for each specialist}
--- {model_name} ({provider}) ---
{response}
{end for}

Your task:
1. Identify factually correct information across all responses
2. Identify the most complete and detailed answer
3. Correct any errors or inconsistencies you detect
4. Combine the best parts into one final, complete, accurate answer
5. Do not mention which model said what — just give the best answer

Final Answer:
```

---

## 7. API Endpoints

```
GET  /api/ollama/models          — List available Ollama models
POST /api/chat                   — Start a MoA chat (returns SSE stream)
GET  /api/conversations          — List all conversations
GET  /api/conversations/{id}     — Get full conversation with responses
DELETE /api/conversations/{id}   — Delete conversation
GET  /api/stats/models           — Aggregate model performance stats
POST /api/config/save            — Save model config
GET  /api/config/list            — List saved configs
POST /api/keys                   — Save API key
GET  /api/health                 — Health check all providers
GET  /api/export/{id}            — Export conversation as MD or JSON
```

---

## 8. Frontend Component Tree

```
App
├── Layout
│   ├── Sidebar
│   │   ├── NewChatButton
│   │   ├── ConversationList
│   │   └── SettingsLink
│   └── MainContent
│       ├── SetupScreen
│       │   ├── ProviderSelector
│       │   ├── SpecialistPicker
│       │   │   ├── OllamaCheckboxes
│       │   │   └── CloudModelInputs
│       │   ├── ChairmanSelector
│       │   └── PipelineModeSelector
│       └── ChatScreen
│           ├── SpecialistGrid
│           │   └── SpecialistCard (×N)
│           │       ├── ModelBadge
│           │       ├── StreamingText
│           │       └── StatsBar (tok/s, latency)
│           ├── ChairmanPanel
│           │   └── FinalAnswer
│           └── InputBar
└── SettingsPage
    ├── APIKeyManager
    ├── ModelStatsPanel
    └── ExportPanel
```

---

## 9. Config File (Local)

```json
// ~/.moa/config.json
{
  "keys": {
    "openrouter": "sk-or-...",
    "bytez": "btz-..."
  },
  "default_pipeline": "parallel",
  "default_specialists": [
    { "model": "dolphin3:8b", "provider": "ollama" },
    { "model": "qwen2.5-coder:7b", "provider": "ollama" }
  ],
  "default_chairman": {
    "model": "google/gemini-flash-1.5",
    "provider": "openrouter"
  }
}
```
