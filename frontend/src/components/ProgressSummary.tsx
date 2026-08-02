import type { CSSProperties } from 'react';
import { ProgressBar } from './ProgressBar';
import { Icon } from './Icon';

type Props = { progress: number; branchCount: number; challengeCount: number };

export function ProgressSummary({ progress, branchCount, challengeCount }: Props) {
  return (
    <section className="summary-card" aria-labelledby="summary-title">
      <div className="progress-ring" style={{ '--progress': String(progress) } as CSSProperties}>
        <div><strong>{progress}%</strong><small>Progreso total</small></div>
      </div>
      <div className="summary-card__copy">
        <h2 id="summary-title">Vas por buen camino, Attune.</h2>
        <p>{branchCount} ramas principales <span>•</span> {challengeCount} desafíos vinculados</p>
        <ProgressBar value={progress} tone="gold" label="Progreso total" />
        <p className="summary-card__caption"><strong>{progress}%</strong> hacia el título</p>
      </div>
      <div className="master-crest" aria-hidden="true"><Icon name="trophy" size={48} /></div>
    </section>
  );
}
