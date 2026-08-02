import type { Branch } from '../types';
import { Icon } from './Icon';
import { ProgressBar } from './ProgressBar';

type Props = {
  branch: Branch;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onOpenTree: () => void;
};

export function BranchCard({ branch, isSelected, onSelect, onOpenTree }: Props) {
  return (
    <article id={branch.id} className={`branch-card branch-card--${branch.tone} ${isSelected ? 'is-selected' : ''}`}>
      <button className="branch-card__select" type="button" onClick={() => onSelect(branch.id)} aria-label={`Seleccionar ${branch.name}`}>
        <span className="branch-card__icon"><Icon name={branch.icon} size={29} /></span>
        <h3>{branch.name}</h3>
        <p>{branch.rank}</p>
        <strong>{branch.progress}%</strong>
        <ProgressBar value={branch.progress} tone={branch.tone} label={`Progreso de ${branch.name}`} />
        {branch.hasChildren === false ? <span className="branch-card__cta branch-card__cta--final" title={branch.description || `Completá ${branch.name} para alcanzar este objetivo.`}>Objetivo final</span> : <span className="branch-card__cta" onClick={(event) => { event.stopPropagation(); onOpenTree(); }}>Ver más <Icon name="chevron-right" size={16} /></span>}
      </button>
    </article>
  );
}
