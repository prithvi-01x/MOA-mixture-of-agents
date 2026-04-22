const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// --- Types ---

export interface HealthStatus {
  groq: boolean;
  openrouter: boolean;
}

export interface GroqModelsResponse {
  models: string[];
}

export interface OpenRouterModelsResponse {
  models: string[];
}

export interface Conversation {
  id: string;
  title: string;
  pipeline_mode: string;
  created_at: string;
  updated_at: string;
}

export interface SpecialistConfig {
  model: string;
  provider: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChairmanConfig {
  model: string;
  provider: string;
}

export interface ChatRequest {
  query: string;
  specialists: SpecialistConfig[];
  chairman: ChairmanConfig;
  pipeline_mode?: string;
  conversation_id?: string | null;
}

export interface SSECallbacks {
  onSpecialistToken: (model: string, provider: string, token: string) => void;
  onSpecialistDone: (model: string, provider: string, content: string, tokPerSec: number, latencyMs: number, error?: string) => void;
  onChairmanStart?: () => void;
  onChairmanToken: (token: string) => void;
  onChairmanDone: () => void;
  onConversationId?: (id: string) => void;
  onError: (message: string) => void;
}

// --- API functions ---

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  health: (): Promise<HealthStatus> => get('/api/health'),

  groqModels: (): Promise<GroqModelsResponse> => get('/api/groq/models'),

  openrouterModels: (): Promise<OpenRouterModelsResponse> => get('/api/openrouter/models'),

  setKey: (provider: string, key: string): Promise<{ success: boolean }> =>
    post('/api/keys', { provider, key }),

  getKey: (provider: string): Promise<{ provider: string; key: string | null }> =>
    get(`/api/keys/${provider}`),

  conversations: (): Promise<Conversation[]> => get('/api/conversations'),

  /**
   * Start a streaming chat request. Returns a cleanup function that aborts the stream.
   */
  startChat(request: ChatRequest, callbacks: SSECallbacks): () => void {
    const controller = new AbortController();

    (async () => {
      try {
        const res = await fetch(`${BASE}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          callbacks.onError(`HTTP ${res.status}`);
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr);
              switch (event.type) {
                case 'conversation_id':
                  callbacks.onConversationId?.(event.conversation_id);
                  break;
                case 'specialist_token':
                  callbacks.onSpecialistToken(
                    event.model,
                    event.provider,
                    event.content ?? '',
                  );
                  break;
                case 'specialist_done':
                  callbacks.onSpecialistDone(
                    event.model,
                    event.provider,
                    event.content,
                    event.tokens_per_sec ?? 0,
                    event.latency_ms ?? 0,
                    event.error ?? undefined,
                  );
                  break;
                case 'chairman_start':
                  callbacks.onChairmanStart?.();
                  break;
                case 'chairman_token':
                  callbacks.onChairmanToken(event.content ?? '');
                  break;
                case 'chairman_done':
                  callbacks.onChairmanDone();
                  break;
                case 'error':
                  callbacks.onError(event.message ?? 'Unknown error');
                  break;
              }
            } catch {
              // malformed JSON line — skip
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return;
        callbacks.onError(String(err));
      }
    })();

    return () => controller.abort();
  },
};
