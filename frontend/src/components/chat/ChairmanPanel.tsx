import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import { useStore } from '../../store/app';
import ExportMenu from './ExportMenu';

export default function ChairmanPanel() {
  const { chairmanContent, chairmanStreaming, chairmanDone, activeConversationId } = useStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!chairmanContent) return;
    await navigator.clipboard.writeText(chairmanContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isActive = chairmanStreaming || chairmanDone;

  return (
    <div style={{
      background: 'var(--bg-card)',
      borderTop: '2px solid var(--accent)',
      minHeight: 200,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 20px',
        background: 'var(--bg-header)',
        borderBottom: '1px solid var(--border)',
      }}>
        <div>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            fontSize: 12,
            color: 'var(--accent)',
            letterSpacing: '0.1em',
          }}>
            CHAIRMAN
          </span>
          <span style={{
            fontFamily: 'var(--font-body)',
            fontSize: 11,
            color: 'var(--text-dim)',
            marginLeft: 10,
          }}>
            Final Answer Synthesis
          </span>
        </div>
        {/* Squares indicator */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className={i === 2 && chairmanStreaming ? 'pulse' : ''}
              style={{
                width: 8,
                height: 8,
                background: isActive
                  ? i === 2 && chairmanStreaming
                    ? 'var(--accent)'
                    : 'var(--accent)'
                  : 'var(--border-mid)',
                display: 'inline-block',
              }}
            />
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        padding: '20px 24px',
        minHeight: 120,
        overflow: 'auto',
      }}>
        {chairmanContent ? (
          <div className="prose">
            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>{chairmanContent}</ReactMarkdown>
            {chairmanStreaming && (
              <span className="blink" style={{ color: 'var(--accent)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>▋</span>
            )}
          </div>
        ) : (
          <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            {chairmanStreaming
              ? <span className="blink" style={{ color: 'var(--accent)', fontWeight: 700 }}>▋</span>
              : isActive
              ? 'Processing...'
              : 'Waiting for specialists to complete...'}
          </span>
        )}
      </div>

      {/* Footer */}
      {(chairmanDone || chairmanContent) && (
        <div style={{
          padding: '10px 20px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 8,
        }}>
          <ExportMenu
            conversationId={activeConversationId}
            markdownContent={chairmanContent}
          />
          <button
            onClick={handleCopy}
            style={{
              background: 'transparent',
              border: `1px solid ${copied ? 'var(--accent)' : 'var(--border-mid)'}`,
              color: copied ? 'var(--accent)' : 'var(--text-dim)',
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              fontWeight: 600,
              padding: '5px 12px',
              cursor: 'pointer',
              letterSpacing: '0.1em',
            }}
          >
            {copied ? '✓ COPIED' : '[ COPY ]'}
          </button>
        </div>
      )}
    </div>
  );
}
