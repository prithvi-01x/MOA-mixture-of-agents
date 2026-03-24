import { useState } from 'react';
import toast from 'react-hot-toast';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ExportMenuProps {
  conversationId: string | null;
  /** Optional: plain-text content to offer for "copy as markdown" */
  markdownContent?: string;
}

/**
 * Dropdown export menu for conversation download and clipboard copy.
 * Renders a compact button that opens a 3-item dropdown.
 */
export default function ExportMenu({ conversationId, markdownContent }: ExportMenuProps) {
  const [open, setOpen] = useState(false);

  const triggerDownload = async (format: 'markdown' | 'json') => {
    if (!conversationId) {
      toast.error('No active conversation to export.');
      return;
    }
    setOpen(false);
    const url = `${BASE}/api/conversations/${conversationId}/export?format=${format}`;
    const ext = format === 'json' ? 'json' : 'md';

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `conversation.${ext}`;
      a.click();
      URL.revokeObjectURL(blobUrl);
      toast.success(`Exported as ${ext.toUpperCase()}`);
    } catch (err) {
      toast.error(`Export failed: ${String(err)}`);
    }
  };

  const handleCopy = async () => {
    setOpen(false);
    const content = markdownContent ?? '';
    if (!content) {
      toast.error('Nothing to copy yet.');
      return;
    }
    try {
      await navigator.clipboard.writeText(content);
      toast.success('Copied to clipboard');
    } catch {
      toast.error('Clipboard write failed');
    }
  };

  const btnStyle: React.CSSProperties = {
    display: 'block',
    width: '100%',
    background: 'transparent',
    border: 'none',
    color: 'var(--text-dim)',
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    letterSpacing: '0.06em',
    padding: '7px 14px',
    textAlign: 'left',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={!conversationId}
        style={{
          background: 'transparent',
          border: `1px solid var(--border-mid)`,
          color: conversationId ? 'var(--text-dim)' : '#444',
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          fontWeight: 600,
          padding: '5px 12px',
          cursor: conversationId ? 'pointer' : 'not-allowed',
          letterSpacing: '0.1em',
          display: 'flex',
          alignItems: 'center',
          gap: 5,
        }}
      >
        [ EXPORT ▾ ]
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setOpen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 10 }}
          />
          {/* Dropdown */}
          <div style={{
            position: 'absolute',
            bottom: '100%',
            right: 0,
            marginBottom: 4,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-mid)',
            zIndex: 20,
            minWidth: 170,
          }}>
            <button
              style={btnStyle}
              onClick={() => triggerDownload('markdown')}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
            >
              ↓ Export as Markdown
            </button>
            <div style={{ height: 1, background: 'var(--border)' }} />
            <button
              style={btnStyle}
              onClick={() => triggerDownload('json')}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
            >
              ↓ Export as JSON
            </button>
            <div style={{ height: 1, background: 'var(--border)' }} />
            <button
              style={btnStyle}
              onClick={handleCopy}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--accent)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
            >
              ⎘ Copy as Markdown
            </button>
          </div>
        </>
      )}
    </div>
  );
}
