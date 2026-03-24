/**
 * Component tests for SetupPage.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Stub child components that do network requests
vi.mock('../components/setup/ProviderTabs', () => ({
  default: () => (
    <div>
      <button data-testid="tab-ollama">Ollama</button>
      <button data-testid="tab-openrouter">OpenRouter</button>
      <button data-testid="tab-bytez">Bytez</button>
    </div>
  ),
}));

vi.mock('../components/setup/SpecialistPicker', () => ({
  default: () => <div data-testid="specialist-picker" />,
}));

vi.mock('../components/setup/ChairmanSelector', () => ({
  default: () => <div data-testid="chairman-selector" />,
}));

vi.mock('../components/setup/PipelineModeSelector', () => ({
  default: () => <div data-testid="pipeline-selector" />,
}));

vi.mock('../components/setup/APIKeyPanel', () => ({
  default: () => <div data-testid="api-key-panel" />,
}));

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

const makeStore = (overrides = {}) => ({
  selectedSpecialists: [],
  chairman: { model: '', provider: 'ollama' },
  ollamaModels: [],
  activeProvider: 'ollama',
  toggleSpecialist: vi.fn(),
  ...overrides,
});

vi.mock('../store/app', () => ({
  useStore: vi.fn(),
}));

import { useStore } from '../store/app';
import SetupPage from '../pages/SetupPage';

describe('SetupPage', () => {
  beforeEach(() => {
    (useStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue(makeStore());
  });

  it('renders provider tab buttons', () => {
    render(<MemoryRouter><SetupPage /></MemoryRouter>);
    expect(screen.getByTestId('tab-ollama')).toBeTruthy();
    expect(screen.getByTestId('tab-openrouter')).toBeTruthy();
    expect(screen.getByTestId('tab-bytez')).toBeTruthy();
  });

  it('renders SpecialistPicker', () => {
    render(<MemoryRouter><SetupPage /></MemoryRouter>);
    expect(screen.getByTestId('specialist-picker')).toBeTruthy();
  });

  it('disables Start button when no specialists selected', () => {
    render(<MemoryRouter><SetupPage /></MemoryRouter>);
    // Button text is 'START CHAT →' in the actual component
    const btn = screen.getByText(/START CHAT/i) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });
});
