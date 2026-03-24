import { useStore } from '../../store/app';
import SpecialistCard from './SpecialistCard';

export default function SpecialistGrid() {
  const { specialists } = useStore();

  if (specialists.length === 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: 400,
        background: 'var(--bg-card)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--text-dim)',
        letterSpacing: '0.06em',
      }}>
        NO SPECIALISTS ACTIVE
      </div>
    );
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${Math.min(specialists.length, 3)}, 1fr)`,
      gap: 1,
      background: '#1a1a1a',
    }}>
      {specialists.map((s) => (
        <SpecialistCard key={`${s.provider}:${s.model}`} specialist={s} />
      ))}
    </div>
  );
}
