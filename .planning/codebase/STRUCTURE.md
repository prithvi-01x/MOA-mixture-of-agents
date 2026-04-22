# Codebase Structure

**Analysis Date:** 2025-05-15

## Directory Layout

```
MOA-mixture-of-agents/
├── frontend/           # React + TypeScript Vite frontend
│   ├── src/            # Frontend source code
│   │   ├── components/ # UI components (chat, setup, etc.)
│   │   ├── layouts/    # Page layouts
│   │   ├── lib/        # API client and utilities
│   │   ├── pages/      # Main pages (SetupPage, ChatPage)
│   │   └── store/      # Zustand state management
│   ├── public/         # Static assets
│   └── tests/          # Frontend tests (Vitest)
├── moa/                # Core MoA pipeline and orchestration logic
├── providers/          # Provider-specific implementations (Ollama, OpenRouter, Bytez)
├── routers/            # FastAPI router modules (chat, models, keys, etc.)
├── tests/              # Backend integration and unit tests (Pytest)
├── docs/               # Project documentation
├── main.py             # Backend entry point
├── database.py         # SQLite database interaction
├── config.py           # Application configuration
├── logger.py           # Logging utility
└── requirements.txt    # Python dependencies
```

## Directory Purposes

**`frontend/`:**
- Purpose: The user interface.
- Contains: React components, hooks, styles, and state management logic.
- Key files: `frontend/src/App.tsx` (main layout), `frontend/src/store/app.ts` (state management), `frontend/src/lib/api.ts` (API interaction).

**`moa/`:**
- Purpose: Core MoA orchestration logic.
- Contains: MoA pipeline and chairman aggregation implementations.
- Key files: `moa/pipeline.py` (parallel/serial/debate logic), `moa/chairman.py` (aggregation logic).

**`providers/`:**
- Purpose: Abstraction layer for different LLM providers.
- Contains: Classes for interacting with Ollama, OpenRouter, and Bytez.
- Key files: `providers/base.py` (interface), `providers/factory.py` (provider instantiation).

**`routers/`:**
- Purpose: FastAPI route definitions.
- Contains: API endpoints for chat, model listing, and configuration.
- Key files: `routers/chat.py` (main streaming endpoint).

## Key File Locations

**Entry Points:**
- `main.py`: Backend entry point (FastAPI server).
- `frontend/src/main.tsx`: Frontend entry point.

**Configuration:**
- `config.py`: Backend configuration settings.
- `frontend/package.json`: Frontend dependencies and scripts.

**Core Logic:**
- `moa/pipeline.py`: MoA pipeline orchestration.
- `database.py`: Database operations and schema management.

**Testing:**
- `tests/`: Backend tests.
- `frontend/src/__tests__/`: Frontend tests.

## Naming Conventions

**Files:**
- Backend: `snake_case.py` (e.g., `pipeline_manager.py`).
- Frontend: `PascalCase.tsx` for components (e.g., `SpecialistCard.tsx`), `camelCase.ts` for others (e.g., `api.ts`).

**Directories:**
- All: `snake-case` or `lowercase` (e.g., `chat_components/` or `providers/`).

## Where to Add New Code

**New MoA Strategy:**
- Primary code: `moa/pipeline.py` (add a new method to `MoAPipeline`).
- Frontend integration: `frontend/src/store/app.ts` (update `PipelineMode` type and actions).

**New LLM Provider:**
- Implementation: `providers/` (create a new provider class inheriting from `BaseProvider`).
- Factory: `providers/factory.py` (add the new provider to the `get_provider` logic).

**New UI Component:**
- Implementation: `frontend/src/components/` (categorize as `chat/`, `setup/`, etc.).

**New Backend Route:**
- Implementation: `routers/` (create a new router file and register it in `main.py`).

## Special Directories

**`__pycache__`:**
- Purpose: Compiled Python bytecode.
- Generated: Yes.
- Committed: No.

**`node_modules`:**
- Purpose: Node.js packages.
- Generated: Yes.
- Committed: No.

---

*Structure analysis: 2025-05-15*
