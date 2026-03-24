# Product Requirements Document (PRD)
## MoA — Mixture of Agents App

**Version:** 1.0  
**Status:** Planning  
**Last Updated:** March 2026

---

## 1. Overview

MoA is a local-first web application that routes a single user query to multiple AI specialist models simultaneously (or serially), collects all responses, and uses a designated "chairman" model to aggregate, evaluate, and produce a single final answer. It supports three model providers: Ollama (local), OpenRouter (cloud), and Bytez (HuggingFace serverless).

---

## 2. Problem Statement

Single models have blind spots — a model great at reasoning may write poor code, and a model great at code may miss edge cases in security analysis. Running multiple specialist models and intelligently combining their outputs produces higher quality, more reliable answers than any single model alone.

---

## 3. Goals

- Allow users to configure multiple specialist models from any supported provider
- Run specialists in parallel (async sequential under the hood due to VRAM constraints)
- Use a chairman model to aggregate all specialist outputs into one final answer
- Provide a fast, professional, responsive local web UI
- Store full conversation history locally in SQLite
- Track model performance over time (tok/s, latency, response quality)

---

## 4. Non-Goals

- No cloud deployment or multi-user support
- No mobile app
- No real-time collaboration
- No billing or subscription management

---

## 5. Target User

Solo developer / security researcher running a local GPU machine (RTX 4050 6GB). Needs a tool for cybersecurity research, CTF challenges, code generation, and general reasoning tasks. Values privacy, speed, and professional UI.

---

## 6. Supported Providers

| Provider | Type | Auth | Notes |
|---|---|---|---|
| Ollama | Local | None | Auto-detect models via REST API |
| OpenRouter | Cloud | API Key | 300+ models, free tier available |
| Bytez | Cloud | API Key | 220k+ HuggingFace models, serverless |

---

## 7. Core Features

### 7.1 Model Selection (Priority: Critical)
- Ollama: auto-detect available models, display as checkboxes
- OpenRouter / Bytez: text input fields for model names
- Mixed provider support (e.g. Ollama specialists + OpenRouter chairman)
- Chairman model: separate manual selection with provider toggle

### 7.2 Pipeline Modes (Priority: High)
- **Parallel Mode**: All specialists queried simultaneously, chairman aggregates
- **Serial Mode**: Each model builds on the previous model's output
- **Debate Mode**: Models critique each other's responses before chairman decides

### 7.3 Streaming Responses (Priority: Critical)
- Ollama: chunked HTTP streaming
- OpenRouter: Server-Sent Events (SSE)
- Bytez: polling (no native streaming)
- UI shows live streaming per specialist card

### 7.4 Chairman Aggregation (Priority: High)
- Receives all specialist outputs
- Combines best parts, corrects errors, produces final answer
- Uses a well-engineered system prompt
- Recommended: use OpenRouter free model (e.g. Gemini Flash) as chairman

### 7.5 Conversation History (Priority: Medium)
- All sessions stored in SQLite
- Sidebar to browse past conversations
- Full message + per-model response storage

### 7.6 Model Performance Tracking (Priority: Medium)
- Track tokens/sec per model per response
- Track latency (time to first token, total time)
- Viewable in a stats panel

### 7.7 Per-model System Prompts (Priority: Medium)
- Each specialist can have a custom system prompt
- Configurable in model selection screen

### 7.8 API Key Management (Priority: High)
- Secure local storage for OpenRouter and Bytez keys
- Keys stored in local config file, never sent anywhere except the respective provider

### 7.9 Response Rating (Priority: Low)
- User can rate final chairman output (thumbs up/down or 1-5)
- Ratings stored in SQLite for future reference

### 7.10 Export Conversations (Priority: Low)
- Export full conversation as Markdown or JSON
- Includes per-model responses + chairman output

---

## 8. User Flows

### Flow 1 — First Launch
1. App opens to Setup screen
2. User adds API keys for OpenRouter and/or Bytez (optional)
3. User proceeds to Model Selection

### Flow 2 — Model Selection
1. User selects provider for specialists (Ollama / OpenRouter / Bytez)
2. Ollama: checkboxes with auto-detected models
3. OpenRouter/Bytez: text input fields for model names
4. User selects chairman model and provider
5. User sets pipeline mode (parallel / serial / debate)
6. User starts chat

### Flow 3 — Chat
1. User types query
2. All specialist models receive query simultaneously
3. Specialist cards show streaming responses in real time
4. Once all specialists complete, chairman aggregates
5. Final answer displayed prominently
6. Conversation saved to SQLite

---

## 9. Success Metrics

- Query to first specialist token: < 2 seconds
- UI frame rate during streaming: 60fps
- Chairman aggregation quality: subjectively better than any single model
- App startup time: < 1 second

---

## 10. Constraints

- VRAM limit: 6GB RTX 4050 — Ollama models run sequentially, not truly parallel
- Local only: no internet required except for OpenRouter/Bytez calls
- Single user: no auth system needed
