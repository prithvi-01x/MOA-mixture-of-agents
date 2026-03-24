import { useState } from 'react';
import { useStore } from '../../store/app';
import { api } from '../../lib/api';

const KEYS: { provider: 'openrouter' | 'bytez'; label: string; badge: string; required: boolean }[] = [
  { provider: 'openrouter', label: 'OPENROUTER API KEY', badge: 'REQUIRED FOR CLOUD', required: true },
  { provider: 'bytez', label: 'BYTEZ PLATFORM KEY', badge: 'OPTIONAL', required: false },
];

export default function APIKeyPanel() {
  const { apiKeys, setApiKey } = useStore();
  const [inputs, setInputs] = useState<Record<string, string>>({ openrouter: '', bytez: '' });
  const [saved, setSaved] = useState<Record<string, boolean>>({});

  const handleSave = async (provider: 'openrouter' | 'bytez') => {
    const key = inputs[provider];
    if (!key.trim()) return;
    try {
      await api.setKey(provider, key);
      setApiKey(provider, key);
      setSaved((p) => ({ ...p, [provider]: true }));
      setTimeout(() => setSaved((p) => ({ ...p, [provider]: false })), 2000);
    } catch {
      // silent fail
    }
  };

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)', letterSpacing: '0.1em', marginBottom: 12 }}>
        API GATEWAY INTEGRATION
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {KEYS.map(({ provider, label, badge, required }) => (
          <div key={provider}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)', letterSpacing: '0.06em' }}>
                {label}
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 8,
                color: required ? 'var(--accent)' : 'var(--text-dim)',
                border: `1px solid ${required ? 'var(--accent-border)' : 'var(--border)'}`,
                padding: '1px 4px',
                letterSpacing: '0.06em',
              }}>
                {badge}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 0 }}>
              <input
                type="password"
                className="input-bottom"
                placeholder={apiKeys[provider] ? '••••••••••••' : 'sk-...'}
                value={inputs[provider]}
                onChange={(e) => setInputs((p) => ({ ...p, [provider]: e.target.value }))}
                style={{ flex: 1 }}
              />
              <button
                onClick={() => handleSave(provider)}
                style={{
                  background: saved[provider] ? 'var(--accent)' : 'transparent',
                  border: 'none',
                  borderBottom: `1px solid ${saved[provider] ? 'var(--accent)' : 'var(--border-mid)'}`,
                  color: saved[provider] ? '#000' : 'var(--text-dim)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 9,
                  fontWeight: 700,
                  padding: '0 12px',
                  cursor: 'pointer',
                  letterSpacing: '0.06em',
                }}
              >
                {saved[provider] ? 'SAVED' : 'SAVE'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
