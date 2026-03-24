import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/app';
import ProviderTabs from '../components/setup/ProviderTabs';
import SpecialistPicker from '../components/setup/SpecialistPicker';
import ChairmanSelector from '../components/setup/ChairmanSelector';
import PipelineModeSelector from '../components/setup/PipelineModeSelector';
import APIKeyPanel from '../components/setup/APIKeyPanel';
import { Terminal, Activity, Cpu } from 'lucide-react';

export default function SetupPage() {
  const navigate = useNavigate();
  const { selectedSpecialists, chairman } = useStore();

  const canStart = selectedSpecialists.length > 0 && chairman.model;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'auto' }}>
        {/* LEFT COLUMN */}
        <div style={{
          flex: 1,
          padding: '24px',
          borderRight: '1px solid var(--border)',
          overflow: 'auto',
        }}>
          {/* Label */}
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent)', letterSpacing: '0.1em', marginBottom: 8 }}>
            configure
          </div>
          <h1 style={{
            fontFamily: 'var(--font-headline)',
            fontWeight: 700,
            fontSize: 24,
            color: 'var(--text)',
            margin: '0 0 20px',
            letterSpacing: '-0.02em',
          }}>
            Select Models
          </h1>
          <ProviderTabs />
          <SpecialistPicker />
          <ChairmanSelector />
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
          <PipelineModeSelector />
          <div style={{ marginTop: 24 }}>
            <APIKeyPanel />
          </div>

          {/* Stats grid */}
          <div style={{ marginTop: 24 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)', letterSpacing: '0.1em', marginBottom: 10 }}>
              SYSTEM STATS
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: 'var(--border)' }}>
              {[
                { label: 'TOTAL CONTEXT', value: '8K' },
                { label: 'EST. LATENCY', value: `~${selectedSpecialists.length * 0.8 + 1.2}S` },
                { label: 'SPECIALISTS', value: String(selectedSpecialists.length) },
                { label: 'STATE', value: canStart ? 'READY' : 'CONFIG' },
              ].map(({ label, value }) => (
                <div key={label} style={{
                  background: 'var(--bg-card)',
                  padding: '14px 16px',
                }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-dim)', letterSpacing: '0.1em', marginBottom: 4 }}>
                    {label}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--accent)' }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fixed footer */}
      <div style={{
        height: 56,
        background: 'var(--bg-panel)',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        gap: 12,
        flexShrink: 0,
      }}>
        {/* Left */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          <span className="pulse" style={{
            width: 7, height: 7,
            background: selectedSpecialists.length > 0 ? 'var(--accent)' : 'var(--border-mid)',
            borderRadius: '50% !important' as unknown as string,
            display: 'inline-block',
            flexShrink: 0,
          }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)', letterSpacing: '0.06em' }}>
            {selectedSpecialists.length} SPECIALISTS SELECTED
          </span>
          {selectedSpecialists.length > 0 && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-dim)' }}>
              · {selectedSpecialists.map((s) => s.model.split(':')[0].toUpperCase()).join(' + ')}
            </span>
          )}
        </div>
        {/* Right */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-dim)', padding: '6px 8px', cursor: 'pointer' }}>
            <Terminal size={12} />
          </button>
          <button style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-dim)', padding: '6px 8px', cursor: 'pointer' }}>
            <Activity size={12} />
          </button>
          <button style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-dim)', padding: '6px 8px', cursor: 'pointer' }}>
            <Cpu size={12} />
          </button>
          <button
            onClick={() => canStart && navigate('/chat')}
            disabled={!canStart}
            style={{
              background: canStart ? 'var(--accent)' : 'var(--border)',
              border: 'none',
              color: canStart ? '#000' : 'var(--text-dim)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 700,
              padding: '8px 16px',
              cursor: canStart ? 'pointer' : 'not-allowed',
              letterSpacing: '0.06em',
            }}
          >
            START CHAT →
          </button>
        </div>
      </div>
    </div>
  );
}
