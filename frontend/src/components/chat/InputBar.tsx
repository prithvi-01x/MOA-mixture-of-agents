import { useRef, useState } from 'react';
import { useStore } from '../../store/app';
import { api } from '../../lib/api';

export default function InputBar() {
  const {
    isRunning, selectedSpecialists, chairman, pipelineMode,
    activeConversationId,
    startRun, onSpecialistToken, onSpecialistDone, onChairmanStart,
    onChairmanToken, onChairmanDone, onConversationId, onError,
  } = useStore();
  const [query, setQuery] = useState('');
  const cleanupRef = useRef<(() => void) | null>(null);

  const handleSend = () => {
    const q = query.trim();
    if (!q || isRunning || selectedSpecialists.length === 0) return;

    setQuery('');
    startRun(q, selectedSpecialists);

    const cleanup = api.startChat(
      {
        query: q,
        specialists: selectedSpecialists,
        chairman,
        pipeline_mode: pipelineMode,
        conversation_id: activeConversationId ?? undefined,
      },
      {
        onSpecialistToken,
        onSpecialistDone,
        onChairmanStart,
        onChairmanToken,
        onChairmanDone,
        onConversationId,
        onError,
      },
    );
    cleanupRef.current = cleanup;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      height: 80,
      background: 'var(--bg-panel)',
      borderTop: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 16px',
      gap: 10,
      flexShrink: 0,
    }}>
      <div style={{ flex: 1, position: 'relative' }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRunning}
          placeholder="Ask your specialists..."
          style={{
            width: '100%',
            height: 56,
            background: 'var(--bg-header)',
            border: 'none',
            borderBottom: '1px solid var(--border-mid)',
            color: 'var(--text)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            padding: '10px 12px 20px',
            resize: 'none',
            display: 'block',
            lineHeight: 1.5,
          }}
          onFocus={(e) => (e.target.style.borderBottomColor = 'var(--accent)')}
          onBlur={(e) => (e.target.style.borderBottomColor = 'var(--border-mid)')}
        />
        <span style={{
          position: 'absolute',
          bottom: 6,
          right: 8,
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          color: 'var(--text-dim)',
          pointerEvents: 'none',
          letterSpacing: '0.04em',
        }}>
          CMD+ENTER
        </span>
      </div>
      <button
        onClick={handleSend}
        disabled={isRunning || !query.trim() || selectedSpecialists.length === 0}
        style={{
          width: 48,
          height: 48,
          background: isRunning ? 'var(--border-mid)' : 'var(--accent)',
          border: 'none',
          color: '#000',
          fontSize: 18,
          fontWeight: 700,
          cursor: isRunning ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        →
      </button>
    </div>
  );
}
