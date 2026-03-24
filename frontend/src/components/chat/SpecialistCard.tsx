import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import type { SpecialistState } from '../../store/app';

function ProviderBadge({ provider }: { provider: string }) {
  const colors: Record<string, { bg: string; color: string }> = {
    ollama: { bg: 'rgba(120,120,120,0.15)', color: '#9a9a9a' },
    openrouter: { bg: 'rgba(59,130,246,0.1)', color: '#60a5fa' },
    bytez: { bg: 'rgba(168,85,247,0.1)', color: '#c084fc' },
  };
  const style = colors[provider] ?? colors.ollama;

  return (
    <span style={{
      fontFamily: 'var(--font-mono)',
      fontSize: 8,
      fontWeight: 600,
      letterSpacing: '0.08em',
      padding: '2px 5px',
      background: style.bg,
      color: style.color,
      textTransform: 'uppercase',
    }}>
      {provider}
    </span>
  );
}

export default function SpecialistCard({ specialist }: { specialist: SpecialistState }) {
  const { model, provider, content, isStreaming, isDone, tokPerSec, latencyMs, error } = specialist;

  return (
    <div style={{
      height: 400,
      background: error ? 'rgba(239,68,68,0.06)' : 'var(--bg-card)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        height: 48,
        background: error ? 'rgba(239,68,68,0.10)' : 'var(--bg-header)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 14px',
        gap: 8,
        flexShrink: 0,
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          fontWeight: 700,
          color: error ? '#f87171' : 'var(--text)',
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          flex: 1,
        }}>
          {model}
        </span>
        <ProviderBadge provider={provider} />
        {/* Status */}
        <div style={{ width: 20, display: 'flex', justifyContent: 'center' }}>
          {error ? (
            <span style={{ color: '#ef4444', fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700 }}>✗</span>
          ) : isDone ? (
            <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700 }}>✓</span>
          ) : (
            <span className="pulse" style={{
              width: 6, height: 6,
              background: '#f59e0b',
              borderRadius: '50% !important' as unknown as string,
              display: 'inline-block',
            }} />
          )}
        </div>
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        background: error ? 'rgba(239,68,68,0.04)' : 'var(--bg-card-inner)',
        padding: '14px',
        overflow: 'auto',
        position: 'relative',
      }}>
        {error ? (
          <div>
            <div style={{ color: '#ef4444', fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.08em', marginBottom: 8 }}>
              SPECIALIST ERROR
            </div>
            <div style={{ color: '#fca5a5', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{error}</div>
          </div>
        ) : content ? (
          <div className="prose">
            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>{content}</ReactMarkdown>
            {isStreaming && (
              <span className="blink" style={{ color: 'var(--accent)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>▋</span>
            )}
          </div>
        ) : (
          <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            {isStreaming ? (
              <span className="blink" style={{ color: 'var(--accent)', fontWeight: 700 }}>▋</span>
            ) : 'Waiting...'}
          </span>
        )}
      </div>

      {/* Footer */}
      <div style={{
        height: 40,
        background: error ? 'rgba(239,68,68,0.10)' : 'var(--bg-header)',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 14px',
        flexShrink: 0,
      }}>
        {error ? (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#ef4444', fontWeight: 700, letterSpacing: '0.06em' }}>
            ERROR
          </span>
        ) : isDone ? (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)', letterSpacing: '0.06em' }}>
            {tokPerSec.toFixed(1)} TOK/S · {latencyMs}MS
          </span>
        ) : isStreaming ? (
          <span className="shimmer" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent)', letterSpacing: '0.06em' }}>
            STREAMING...
          </span>
        ) : (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)' }}>IDLE</span>
        )}
      </div>
    </div>
  );
}
