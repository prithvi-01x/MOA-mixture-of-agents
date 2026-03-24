# MVP Tech Plan
## MoA — Mixture of Agents App

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** March 2026

---

## MVP Scope

The MVP delivers a working end-to-end MoA pipeline with a professional UI. Only the critical and high priority features are included. Everything else is post-MVP.

---

## What's IN the MVP

| Feature | Priority |
|---|---|
| Provider abstraction layer (Ollama, OpenRouter, Bytez) | Critical |
| Streaming responses per specialist | Critical |
| SQLite schema + conversation storage | Critical |
| API key management | High |
| Parallel pipeline mode only | High |
| Ollama auto-detect models (checkboxes) | High |
| OpenRouter + Bytez manual model input | High |
| Chairman model (manual selection) | High |
| Professional UI — setup screen + chat screen | High |
| Model tok/s + latency stats display | High |
| VRAM-safe async sequential execution | High |

## What's NOT in the MVP

| Feature | Reason |
|---|---|
| Serial pipeline mode | Post-MVP |
| Debate pipeline mode | Post-MVP |
| Conversation history sidebar | Post-MVP |
| Per-model system prompts UI | Post-MVP |
| Response rating system | Post-MVP |
| Export conversations | Post-MVP |
| Model performance tracking dashboard | Post-MVP |

---

## Tech Stack

### Frontend
```
Vite 5.x
React 18.x
TailwindCSS 3.x
shadcn/ui
Framer Motion 11.x
```

### Backend
```
Python 3.11+
FastAPI 0.110+
uvicorn (ASGI server)
ollama (Python SDK)
httpx (async HTTP for OpenRouter + Bytez)
aiofiles
sqlite3 (stdlib)
pydantic v2
python-dotenv
```

### Dev Tools
```
pnpm (frontend package manager)
ruff (Python linter)
black (Python formatter)
```

---

## Project Structure

```
moa/
├── backend/
│   ├── main.py                  # FastAPI app, routes
│   ├── config.py                # App config, env vars
│   ├── database.py              # SQLite connection + queries
│   ├── providers/
│   │   ├── base.py              # BaseProvider ABC
│   │   ├── ollama.py            # Ollama implementation
│   │   ├── openrouter.py        # OpenRouter implementation
│   │   └── bytez.py             # Bytez implementation
│   ├── moa/
│   │   ├── pipeline.py          # MoA pipeline logic
│   │   └── chairman.py          # Chairman prompt + aggregation
│   └── routers/
│       ├── chat.py              # /api/chat SSE endpoint
│       ├── models.py            # /api/ollama/models
│       ├── keys.py              # /api/keys
│       └── health.py            # /api/health
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── setup/
│   │   │   │   ├── ProviderSelector.tsx
│   │   │   │   ├── SpecialistPicker.tsx
│   │   │   │   └── ChairmanSelector.tsx
│   │   │   ├── chat/
│   │   │   │   ├── SpecialistCard.tsx
│   │   │   │   ├── SpecialistGrid.tsx
│   │   │   │   ├── ChairmanPanel.tsx
│   │   │   │   └── InputBar.tsx
│   │   │   └── ui/              # shadcn components
│   │   ├── hooks/
│   │   │   ├── useOllamaModels.ts
│   │   │   └── useSSEStream.ts
│   │   ├── lib/
│   │   │   └── api.ts           # Backend API calls
│   │   └── store/
│   │       └── chat.ts          # React state (zustand or useState)
└── README.md
```

---

## Build Phases

### Phase 1 — Backend Foundation (Day 1-2)
- [ ] FastAPI project setup
- [ ] SQLite schema + database.py
- [ ] BaseProvider ABC
- [ ] OllamaProvider (list models + stream)
- [ ] OpenRouterProvider (stream via SSE)
- [ ] BytezProvider (polling)
- [ ] /api/health endpoint
- [ ] /api/ollama/models endpoint
- [ ] /api/keys endpoint

### Phase 2 — MoA Pipeline (Day 3)
- [ ] Parallel pipeline (asyncio.gather)
- [ ] Chairman aggregation prompt
- [ ] SSE streaming endpoint (/api/chat)
- [ ] Per-specialist token stats tracking
- [ ] Error handling per provider

### Phase 3 — Frontend Setup Screen (Day 4)
- [ ] Vite + React + Tailwind + shadcn init
- [ ] ProviderSelector component
- [ ] SpecialistPicker (checkboxes for Ollama, inputs for cloud)
- [ ] ChairmanSelector
- [ ] API key input + save
- [ ] Connect to backend health + models endpoints

### Phase 4 — Frontend Chat Screen (Day 5-6)
- [ ] SpecialistGrid layout
- [ ] SpecialistCard with SSE streaming text
- [ ] tok/s + latency stats bar per card
- [ ] ChairmanPanel (final answer)
- [ ] InputBar
- [ ] Loading/error states

### Phase 5 — Polish + Testing (Day 7)
- [ ] Professional UI polish
- [ ] Error handling UI (model unavailable, API key invalid)
- [ ] Test all three providers end-to-end
- [ ] Test parallel pipeline with mixed providers
- [ ] README with setup instructions

---

## Environment Setup

### Backend
```bash
cd moa/backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn ollama httpx aiofiles pydantic python-dotenv

uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd moa/frontend
pnpm create vite . --template react-ts
pnpm install
pnpm dlx shadcn@latest init
pnpm install framer-motion

pnpm dev  # runs on :5173
```

### Environment Variables
```bash
# backend/.env
OLLAMA_BASE_URL=http://localhost:11434
CONFIG_PATH=~/.moa/config.json
DB_PATH=~/.moa/moa.db
```

---

## MVP Success Criteria

- [ ] User can select Ollama models from auto-detected list
- [ ] User can input OpenRouter and Bytez model names manually
- [ ] User can select chairman model from any provider
- [ ] Query fires to all specialists, streams tokens in real time
- [ ] Chairman produces final aggregated answer
- [ ] All conversations saved to SQLite
- [ ] tok/s and latency shown per specialist card
- [ ] App runs fully offline when only Ollama is used
- [ ] No crashes on 6GB VRAM with 3 Ollama specialists
