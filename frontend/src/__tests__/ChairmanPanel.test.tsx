/**
 * Component tests for ChairmanPanel.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ChairmanPanel from '../components/chat/ChairmanPanel';

// Stub markdown so we only test component logic
vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <span data-testid="md">{children}</span>,
}));
vi.mock('rehype-highlight', () => ({ default: () => {} }));

// Mock ExportMenu so we can detect it renders
vi.mock('../components/chat/ExportMenu', () => ({
  default: ({ conversationId }: { conversationId: string | null }) => (
    <div data-testid="export-menu" data-conv-id={conversationId ?? 'null'} />
  ),
}));

// Stub clipboard API
Object.assign(navigator, {
  clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
});

vi.mock('../store/app', () => ({
  useStore: vi.fn(),
}));

import { useStore } from '../store/app';

const defaultStore = {
  chairmanContent: '',
  chairmanStreaming: false,
  chairmanDone: false,
  activeConversationId: null,
};

describe('ChairmanPanel', () => {
  beforeEach(() => {
    (useStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue(defaultStore);
  });

  it('shows "Waiting for specialists..." before chairman starts', () => {
    render(<ChairmanPanel />);
    expect(screen.getByText(/waiting for specialists/i)).toBeTruthy();
  });

  it('shows streaming cursor when chairmanStreaming is true', () => {
    (useStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultStore,
      chairmanStreaming: true,
      chairmanContent: 'Hello',
    });
    render(<ChairmanPanel />);
    // The blink cursor is rendered as a sibling span with class "blink"
    const cursor = document.querySelector('.blink');
    expect(cursor).toBeTruthy();
  });

  it('export menu appears when chairmanDone is true', () => {
    (useStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultStore,
      chairmanContent: 'Done text',
      chairmanDone: true,
    });
    render(<ChairmanPanel />);
    expect(screen.getByTestId('export-menu')).toBeTruthy();
  });

  it('copy button calls navigator.clipboard.writeText', async () => {
    (useStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      ...defaultStore,
      chairmanContent: 'Copy me',
      chairmanDone: true,
    });
    render(<ChairmanPanel />);
    // The inline copy button renders as "[ COPY ]"
    const copyBtns = screen.getAllByText(/copy/i);
    // Click the one that contains brackets — the inline copy button
    const inlineCopy = copyBtns.find((el) => el.textContent?.includes('['));
    fireEvent.click(inlineCopy!);
    await new Promise((r) => setTimeout(r, 10));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Copy me');
  });
});
