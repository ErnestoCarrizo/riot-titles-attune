import type { Branch } from '../types';
import { Icon } from './Icon';
import { ProgressBar } from './ProgressBar';

type Props = { title: string; rank: string; description: string; branches: Branch[] };

function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return Number.isInteger(value) ? String(value) : value.toLocaleString('es-AR', { maximumFractionDigits: 2 });
}

function metricLabel(branch: Branch): string {
  if (branch.targetValue === null || branch.targetValue === undefined) return 'Cantidad no calculable';
  const remaining = branch.remainingValue === null || branch.remainingValue === undefined
    ? ''
    : ` · faltan ${formatValue(Math.max(0, branch.remainingValue))}`;
  return `${formatValue(branch.currentValue)} / ${formatValue(branch.targetValue)}${remaining}`;
}

export function DetailPanel({ title, rank, description, branches }: Props) {
  return (
    <section className="detail-panel" aria-labelledby="selected-node-title">
      <div className="detail-panel__intro">
        <p className="eyebrow eyebrow--gold">Nodo seleccionado</p>
        <h2 id="selected-node-title">{title}</h2>
        <span className="rank-pill">{rank}</span>
        <p>{description}</p>
      </div>

      <div className="detail-panel__divider"><span><Icon name="chevron-right" size={20} /></span></div>

      <div className="dependencies">
        <p className="eyebrow eyebrow--gold">Dependencias directas</p>
        <div className="dependencies__list">
          {branches.map((branch) => (
            <article
              className="dependency dependency--tooltip"
              key={branch.id}
              tabIndex={0}
              data-tooltip={branch.description || `Completá ${branch.name} para avanzar hacia ${branch.rank}.`}
              aria-label={`${branch.name}. ${branch.description || `Completá este objetivo para avanzar hacia ${branch.rank}.`}`}
            >
              <span className={`mini-icon mini-icon--${branch.tone}`}><Icon name={branch.icon} size={20} /></span>
              <div className="dependency__copy">
                <strong>{branch.name}</strong>
                <small className={`tone-${branch.tone}`}>{branch.rank}</small>
                <em>{metricLabel(branch)}</em>
              </div>
              <ProgressBar value={branch.progress} tone={branch.tone} label={`Dependencia ${branch.name}`} />
              <b>{branch.progress}%</b>
              <span className={`dependency__status dependency__status--${branch.status}`}>
                {branch.status === 'unlocked' ? <Icon name="check" size={15} /> : null}
              </span>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
