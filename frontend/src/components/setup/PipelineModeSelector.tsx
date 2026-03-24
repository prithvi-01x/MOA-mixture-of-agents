import { useStore, type PipelineMode } from '../../store/app';

const MODES: { id: PipelineMode; label: string; desc: string; mvp: boolean }[] = [
  { id: 'parallel', label: 'PARALLEL', desc: 'All specialists run simultaneously', mvp: false },
  { id: 'serial', label: 'SERIAL CHAIN', desc: 'Each specialist builds on the previous output', mvp: true },
  { id: 'debate', label: 'MULTI-AGENT DEBATE', desc: 'Specialists critique each others answers', mvp: true },
];

export default function PipelineModeSelector() {
  const { pipelineMode, setPipelineMode } = useStore();

  return (
    <div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)', letterSpacing: '0.1em', marginBottom: 8 }}>
        PIPELINE MODE
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {MODES.map(({ id, label, desc, mvp }) => {
          const isActive = !mvp && pipelineMode === id;
          return (
            <div
              key={id}
              onClick={() => !mvp && setPipelineMode(id)}
              style={{
                padding: '12px 14px',
                border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                background: isActive ? 'var(--accent-dim)' : 'var(--bg-card)',
                cursor: mvp ? 'not-allowed' : 'pointer',
                opacity: mvp ? 0.5 : 1,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 10,
                  height: 10,
                  border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border-mid)'}`,
                  background: isActive ? 'var(--accent)' : 'transparent',
                  flexShrink: 0,
                }} />
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  fontWeight: 700,
                  color: isActive ? 'var(--accent)' : 'var(--text)',
                  letterSpacing: '0.06em',
                }}>
                  {label}
                </span>
                {mvp && (
                  <span style={{
                    marginLeft: 'auto',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 8,
                    color: 'var(--text-dim)',
                    background: 'var(--bg-header)',
                    padding: '2px 5px',
                    letterSpacing: '0.06em',
                  }}>
                    POST-MVP
                  </span>
                )}
              </div>
              <div style={{
                fontFamily: 'var(--font-body)',
                fontSize: 11,
                color: 'var(--text-dim)',
                marginTop: 4,
                paddingLeft: 18,
              }}>
                {desc}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
