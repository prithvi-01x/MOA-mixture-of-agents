import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/app';
import SpecialistGrid from '../components/chat/SpecialistGrid';
import ChairmanPanel from '../components/chat/ChairmanPanel';
import InputBar from '../components/chat/InputBar';
import { ArrowLeft } from 'lucide-react';

export default function ChatPage() {
  const navigate = useNavigate();
  const { selectedSpecialists, pipelineMode, isRunning, chairmanStreaming } = useStore();

  const activeCount = selectedSpecialists.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Chat top nav */}
      <div style={{
        height: 44,
        background: 'var(--bg-panel)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        flexShrink: 0,
        gap: 16,
      }}>
        {/* Left: back */}
        <button
          onClick={() => navigate('/setup')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'transparent',
            border: 'none',
            color: 'var(--text-dim)',
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            cursor: 'pointer',
            letterSpacing: '0.06em',
            padding: 0,
          }}
        >
          <ArrowLeft size={11} />
          BACK
        </button>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontWeight: 700,
          fontSize: 11,
          color: 'var(--accent)',
          letterSpacing: '0.08em',
        }}>
          MOA_WORKBENCH
        </span>

        {/* Center tabs */}
        <div style={{ display: 'flex', marginLeft: 'auto' }}>
          {['SESSION_LOG', 'METRICS'].map((tab, i) => (
            <button key={tab} style={{
              background: 'transparent',
              border: 'none',
              borderBottom: i === 0 ? '1px solid var(--accent)' : '1px solid transparent',
              padding: '0 12px',
              height: 44,
              fontFamily: 'var(--font-mono)',
              fontSize: 9,
              color: i === 0 ? 'var(--accent)' : 'var(--text-dim)',
              cursor: 'pointer',
              letterSpacing: '0.06em',
            }}>
              {tab}
            </button>
          ))}
        </div>

        {/* Right: badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 16 }}>
          <span
            className={isRunning || chairmanStreaming ? 'pulse' : ''}
            style={{
              width: 6, height: 6,
              background: isRunning || chairmanStreaming ? 'var(--accent)' : 'var(--border-mid)',
              borderRadius: '50% !important' as unknown as string,
              display: 'inline-block',
            }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)', letterSpacing: '0.06em' }}>
            {activeCount} SPECIALISTS · {pipelineMode.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Specialist grid + chairman — scrollable body */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
        <SpecialistGrid />
        <ChairmanPanel />
      </div>

      {/* Input bar */}
      <InputBar />
    </div>
  );
}
