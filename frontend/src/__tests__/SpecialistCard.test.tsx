/**
 * Component tests for SpecialistCard.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { SpecialistState } from '../store/app';
import SpecialistCard from '../components/chat/SpecialistCard';

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <span data-testid="md">{children}</span>,
}));
vi.mock('rehype-highlight', () => ({ default: () => {} }));

vi.mock('../store/app', () => ({
  useStore: vi.fn(),
}));

const makeState = (overrides: Partial<SpecialistState> = {}): SpecialistState => ({
  model: 'llama3.2',
  provider: 'ollama',
  content: 'Hello **world**',
  isStreaming: false,
  isDone: true,
  tokPerSec: 12.5,
  latencyMs: 300,
  ...overrides,
});

describe('SpecialistCard', () => {
  it('renders model name and provider', () => {
    render(<SpecialistCard specialist={makeState()} />);
    expect(screen.getByText(/llama3.2/i)).toBeTruthy();
    expect(screen.getByText(/ollama/i)).toBeTruthy();
  });

  it('shows streaming indicator when isStreaming is true', () => {
    render(<SpecialistCard specialist={makeState({ isStreaming: true, isDone: false })} />);
    expect(screen.getByText(/STREAMING/i)).toBeTruthy();
  });

  it('renders markdown content via ReactMarkdown', () => {
    render(<SpecialistCard specialist={makeState()} />);
    expect(screen.getByTestId('md')).toBeTruthy();
  });

  it('shows error badge when error is set', () => {
    render(<SpecialistCard specialist={makeState({ error: 'Provider failed', content: '' })} />);
    expect(screen.getByText(/provider failed/i)).toBeTruthy();
  });
});
