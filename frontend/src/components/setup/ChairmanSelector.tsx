import { useState } from 'react';
import { useStore } from '../../store/app';

const OLLAMA_MODELS = ['DOLPHIN3:8B', 'QWEN2.5-CODER:7B', 'MISTRAL:7B', 'GEMMA2:9B'];

export default function ChairmanSelector() {
  const { chairman, setChairman, ollamaModels } = useStore();
  const [isCloud, setIsCloud] = useState(false);
  const models = isCloud
    ? ['meta-llama/llama-3.1-70b-instruct', 'anthropic/claude-3-haiku', 'google/gemini-flash-1.5']
    : ollamaModels.length > 0
    ? ollamaModels
    : OLLAMA_MODELS;

  const handleSelect = (model: string) => {
    setChairman({ model, provider: isCloud ? 'openrouter' : 'ollama' });
  };

  return (
    <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 14 }}>👑</span>
        <span style={{ fontFamily: 'var(--font-headline)', fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>
          CHAIRMAN MODEL
        </span>
        {/* LOCAL/CLOUD toggle */}
        <div style={{ marginLeft: 'auto', display: 'flex', border: '1px solid var(--border-mid)' }}>
          {['LOCAL', 'CLOUD'].map((m) => (
            <button
              key={m}
              onClick={() => { setIsCloud(m === 'CLOUD'); setChairman({ model: '', provider: m === 'CLOUD' ? 'openrouter' : 'ollama' }); }}
              style={{
                padding: '4px 10px',
                background: (m === 'CLOUD') === isCloud ? 'var(--bg-header)' : 'transparent',
                border: 'none',
                color: (m === 'CLOUD') === isCloud ? 'var(--accent)' : 'var(--text-dim)',
                fontFamily: 'var(--font-mono)',
                fontSize: 9,
                cursor: 'pointer',
                letterSpacing: '0.06em',
              }}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 8 }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)', letterSpacing: '0.08em', marginBottom: 6 }}>
          SELECTED EXECUTIVE
        </div>
        <select
          value={chairman.model}
          onChange={(e) => handleSelect(e.target.value)}
          style={{
            width: '100%',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-mid)',
            color: chairman.model ? 'var(--text)' : 'var(--text-dim)',
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            padding: '8px 10px',
            cursor: 'pointer',
            appearance: 'none',
          }}
        >
          <option value="">-- SELECT MODEL --</option>
          {models.map((m) => (
            <option key={m} value={m}>{m.toUpperCase()}</option>
          ))}
        </select>
      </div>

      {chairman.model && (
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--accent)',
          color: '#000',
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          fontWeight: 700,
          padding: '4px 8px',
          letterSpacing: '0.06em',
          marginTop: 4,
        }}>
          <span className="pulse" style={{ width: 5, height: 5, background: '#000', display: 'inline-block', borderRadius: '50% !important' as unknown as string }} />
          {chairman.model.toUpperCase().slice(0, 20)}
        </div>
      )}
    </div>
  );
}
