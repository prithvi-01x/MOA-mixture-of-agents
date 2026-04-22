import { describe, it, expect, beforeEach } from 'vitest';
import { useStore } from '../store/app';

describe('Zustand store', () => {
  beforeEach(() => {
    // Reset store to defaults before each test
    useStore.setState({
      groqModels: [],
      activeProvider: 'groq',
      selectedSpecialists: [],
      chairman: { model: '', provider: 'groq' },
      pipelineMode: 'parallel',
      apiKeys: {},
      conversations: [],
      specialists: [],
      chairmanContent: '',
      chairmanStreaming: false,
      chairmanDone: false,
      isRunning: false,
      currentQuery: '',
      health: { groq: false, openrouter: false },
    });
  });

  // --- Setup actions ---

  it('toggleSpecialist adds a new specialist', () => {
    const specialist = { model: 'llama3', provider: 'groq' };
    useStore.getState().toggleSpecialist(specialist);
    expect(useStore.getState().selectedSpecialists).toHaveLength(1);
    expect(useStore.getState().selectedSpecialists[0].model).toBe('llama3');
  });

  it('toggleSpecialist removes an existing specialist', () => {
    const specialist = { model: 'llama3', provider: 'groq' };
    useStore.getState().toggleSpecialist(specialist);
    useStore.getState().toggleSpecialist(specialist);
    expect(useStore.getState().selectedSpecialists).toHaveLength(0);
  });

  it('setChairman updates the chairman config', () => {
    useStore.getState().setChairman({ model: 'gpt-4', provider: 'openrouter' });
    expect(useStore.getState().chairman.model).toBe('gpt-4');
    expect(useStore.getState().chairman.provider).toBe('openrouter');
  });

  it('setPipelineMode updates the pipeline mode', () => {
    useStore.getState().setPipelineMode('serial');
    expect(useStore.getState().pipelineMode).toBe('serial');
  });

  it('setApiKey stores a key for a provider', () => {
    useStore.getState().setApiKey('openrouter', 'sk-test');
    expect(useStore.getState().apiKeys.openrouter).toBe('sk-test');
  });

  // --- Chat actions ---

  it('startRun initialises chat state', () => {
    const specialists = [
      { model: 'llama3', provider: 'groq' },
      { model: 'gpt-4', provider: 'openrouter' },
    ];
    useStore.getState().startRun('test query', specialists);
    const state = useStore.getState();

    expect(state.isRunning).toBe(true);
    expect(state.currentQuery).toBe('test query');
    expect(state.specialists).toHaveLength(2);
    expect(state.specialists[0].isStreaming).toBe(true);
    expect(state.specialists[0].isDone).toBe(false);
    expect(state.chairmanContent).toBe('');
  });

  it('onSpecialistDone updates the correct specialist', () => {
    const specialists = [
      { model: 'llama3', provider: 'groq' },
      { model: 'gpt-4', provider: 'openrouter' },
    ];
    useStore.getState().startRun('query', specialists);
    useStore.getState().onSpecialistDone('llama3', 'groq', 'Response text', 12.5, 300);

    const s = useStore.getState().specialists;
    const updated = s.find((x) => x.model === 'llama3');
    expect(updated?.content).toBe('Response text');
    expect(updated?.isDone).toBe(true);
    expect(updated?.isStreaming).toBe(false);
    expect(updated?.tokPerSec).toBe(12.5);

    // other specialist untouched
    const other = s.find((x) => x.model === 'gpt-4');
    expect(other?.isStreaming).toBe(true);
  });

  it('onChairmanStart flips chairmanStreaming to true', () => {
    useStore.getState().onChairmanStart();
    expect(useStore.getState().chairmanStreaming).toBe(true);
  });

  it('onChairmanToken appends tokens to chairmanContent', () => {
    useStore.getState().onChairmanToken('Hello');
    useStore.getState().onChairmanToken(' World');
    expect(useStore.getState().chairmanContent).toBe('Hello World');
    expect(useStore.getState().chairmanStreaming).toBe(true);
  });

  it('onChairmanDone finalises the run', () => {
    useStore.getState().startRun('q', [{ model: 'x', provider: 'groq' }]);
    useStore.getState().onChairmanToken('answer');
    useStore.getState().onChairmanDone();
    const state = useStore.getState();

    expect(state.chairmanStreaming).toBe(false);
    expect(state.chairmanDone).toBe(true);
    expect(state.isRunning).toBe(false);
  });

  it('resetChat clears all chat state', () => {
    useStore.getState().startRun('q', [{ model: 'x', provider: 'groq' }]);
    useStore.getState().onChairmanToken('tok');
    useStore.getState().resetChat();
    const state = useStore.getState();

    expect(state.specialists).toHaveLength(0);
    expect(state.chairmanContent).toBe('');
    expect(state.isRunning).toBe(false);
    expect(state.currentQuery).toBe('');
  });

  it('onError stops the run', () => {
    useStore.getState().startRun('q', [{ model: 'x', provider: 'groq' }]);
    useStore.getState().onError('Something broke');
    expect(useStore.getState().isRunning).toBe(false);
  });
});
