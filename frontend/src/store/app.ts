import { create } from 'zustand';
import toast from 'react-hot-toast';
import type { SpecialistConfig, ChairmanConfig, Conversation } from '../lib/api';

// --- Types ---

export type Provider = 'groq' | 'openrouter';
export type PipelineMode = 'parallel' | 'serial' | 'debate';

export interface SpecialistState {
  model: string;
  provider: Provider;
  content: string;
  isStreaming: boolean;
  isDone: boolean;
  tokPerSec: number;
  latencyMs: number;
  error?: string;
}

export interface AppState {
  // Setup state
  groqModels: string[];
  openrouterModels: string[];
  activeProvider: Provider;
  selectedSpecialists: SpecialistConfig[];
  chairman: ChairmanConfig;
  pipelineMode: PipelineMode;
  apiKeys: Record<string, string>;

  // Chat state
  conversations: Conversation[];
  activeConversationId: string | null;   // currently open conversation
  specialists: SpecialistState[];
  chairmanContent: string;
  chairmanStreaming: boolean;
  chairmanDone: boolean;
  isRunning: boolean;
  currentQuery: string;

  // Health
  health: { groq: boolean; openrouter: boolean };

  // Theme
  theme: 'dark' | 'light';

  // Actions
  setGroqModels: (models: string[]) => void;
  setOpenRouterModels: (models: string[]) => void;
  setActiveProvider: (p: Provider) => void;
  toggleSpecialist: (config: SpecialistConfig) => void;
  setChairman: (c: ChairmanConfig) => void;
  setPipelineMode: (m: PipelineMode) => void;
  setApiKey: (provider: string, key: string) => void;
  setHealth: (h: { groq: boolean; openrouter: boolean }) => void;
  setConversations: (c: Conversation[]) => void;
  setCurrentQuery: (q: string) => void;
  setActiveConversationId: (id: string | null) => void;
  updateSpecialistPrompt: (model: string, provider: string, prompt: string) => void;

  // Chat actions
  startRun: (query: string, specialists: SpecialistConfig[]) => void;
  onSpecialistToken: (model: string, provider: string, token: string) => void;
  onSpecialistDone: (model: string, provider: string, content: string, tokPerSec: number, latencyMs: number, error?: string) => void;
  onChairmanStart: () => void;
  onChairmanToken: (token: string) => void;
  onChairmanDone: () => void;
  onConversationId: (id: string) => void;
  onError: (message: string) => void;
  resetChat: () => void;
  newChat: () => void;
  toggleTheme: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Setup defaults
  groqModels: [],
  openrouterModels: [],
  activeProvider: 'groq',
  selectedSpecialists: [],
  chairman: { model: '', provider: 'groq' },
  pipelineMode: 'parallel',
  apiKeys: {},

  // Chat defaults
  conversations: [],
  activeConversationId: null,
  specialists: [],
  chairmanContent: '',
  chairmanStreaming: false,
  chairmanDone: false,
  isRunning: false,
  currentQuery: '',

  health: { groq: false, openrouter: false },

  // Theme: read from localStorage, fall back to 'dark'
  theme: ((): 'dark' | 'light' => {
    const saved = typeof localStorage !== 'undefined'
      ? localStorage.getItem('moa:theme')
      : null;
    return (saved === 'light' ? 'light' : 'dark') as 'dark' | 'light';
  })(),

  // Setup actions
  setGroqModels: (models) => set({ groqModels: models }),
  setOpenRouterModels: (models) => set({ openrouterModels: models }),
  setActiveProvider: (p) => set({ activeProvider: p }),

  toggleSpecialist: (config) => {
    const { selectedSpecialists } = get();
    const exists = selectedSpecialists.some(
      (s) => s.model === config.model && s.provider === config.provider,
    );
    set({
      selectedSpecialists: exists
        ? selectedSpecialists.filter((s) => !(s.model === config.model && s.provider === config.provider))
        : [...selectedSpecialists, config],
    });
  },

  setChairman: (c) => set({ chairman: c }),
  setPipelineMode: (m) => set({ pipelineMode: m }),
  setApiKey: (provider, key) =>
    set((state) => ({ apiKeys: { ...state.apiKeys, [provider]: key } })),
  setHealth: (h) => set({ health: h }),
  setConversations: (c) => set({ conversations: c }),
  setCurrentQuery: (q) => set({ currentQuery: q }),
  setActiveConversationId: (id) => set({ activeConversationId: id }),

  updateSpecialistPrompt: (model, provider, prompt) =>
    set((state) => ({
      selectedSpecialists: state.selectedSpecialists.map((s) =>
        s.model === model && s.provider === provider
          ? { ...s, system_prompt: prompt }
          : s,
      ),
    })),

  // Chat actions
  startRun: (query, specialists) => {
    set({
      isRunning: true,
      currentQuery: query,
      chairmanContent: '',
      chairmanStreaming: false,
      chairmanDone: false,
      specialists: specialists.map((s) => ({
        model: s.model,
        provider: s.provider as Provider,
        content: '',
        isStreaming: true,
        isDone: false,
        tokPerSec: 0,
        latencyMs: 0,
      })),
    });
  },

  // Append a streaming token to the correct specialist's content
  onSpecialistToken: (model, provider, token) => {
    set((state) => ({
      specialists: state.specialists.map((s) =>
        s.model === model && s.provider === provider
          ? { ...s, content: s.content + token }
          : s,
      ),
    }));
  },

  onSpecialistDone: (model, provider, content, tokPerSec, latencyMs, error) => {
    set((state) => ({
      specialists: state.specialists.map((s) =>
        s.model === model && s.provider === provider
          ? { ...s, content, isStreaming: false, isDone: true, tokPerSec, latencyMs, error }
          : s,
      ),
    }));
  },

  onChairmanStart: () => {
    set({ chairmanStreaming: true });
  },

  onChairmanToken: (token) => {
    set((state) => ({
      chairmanContent: state.chairmanContent + token,
      chairmanStreaming: true,
    }));
  },

  onChairmanDone: () => {
    set({ chairmanStreaming: false, chairmanDone: true, isRunning: false });
  },

  onConversationId: (id) => {
    set({ activeConversationId: id });
  },

  onError: (message) => {
    console.error('Chat error:', message);
    toast.error(message, { duration: 5000 });
    set({ isRunning: false });
  },

  resetChat: () => {
    set({
      specialists: [],
      chairmanContent: '',
      chairmanStreaming: false,
      chairmanDone: false,
      isRunning: false,
      currentQuery: '',
    });
  },

  newChat: () => {
    set({
      activeConversationId: null,
      specialists: [],
      chairmanContent: '',
      chairmanStreaming: false,
      chairmanDone: false,
      isRunning: false,
      currentQuery: '',
    });
  },

  toggleTheme: () => {
    const next = get().theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('moa:theme', next);
    set({ theme: next });
  },
}));
