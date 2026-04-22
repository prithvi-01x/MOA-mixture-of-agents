import { useStore, type Provider } from '../../store/app';

const PROVIDERS: { id: Provider; label: string }[] = [
  { id: 'groq', label: 'GROQ' },
  { id: 'openrouter', label: 'OPENROUTER' },
];

export default function ProviderTabs() {
  const { activeProvider, setActiveProvider, health } = useStore();

  return (
    <div style={{ display: 'flex', gap: 0, marginBottom: 16 }}>
      {PROVIDERS.map(({ id, label }) => {
        const isActive = activeProvider === id;
        const isHealthy = health[id];
        return (
          <button
            key={id}
            onClick={() => setActiveProvider(id)}
            style={{
              flex: 1,
              padding: '8px 12px',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
              borderLeft: id !== 'groq' ? 'none' : undefined,
              color: isActive ? 'var(--accent)' : 'var(--text-dim)',
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.06em',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              justifyContent: 'center',
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50% !important' as unknown as string,
                background: isActive && isHealthy ? 'var(--accent)' : isActive ? 'var(--accent-border)' : 'var(--border-mid)',
                display: 'inline-block',
              }}
              className={isActive && isHealthy ? 'pulse' : ''}
            />
            {label}
          </button>
        );
      })}
    </div>
  );
}
