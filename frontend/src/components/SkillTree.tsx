import type { Branch } from '../types';
import { MasterNode } from './MasterNode';
import { BranchCard } from './BranchCard';

interface Props {
  branches: Branch[];
  selectedId: string;
  onSelect: (id: string) => void;
  title: string;
  progress: number;
  rank: string;
  onOpenTree: (id: string) => void;
}

export function SkillTree({ branches, selectedId, onSelect, title, progress, rank, onOpenTree }: Props) {
  return (
    <section className="tree-stage" id="tree" aria-label="Árbol de progreso">
      <div className="tree-stage__orbit" aria-hidden="true" />
      <MasterNode title={title} progress={progress} rank={rank} />
      <div className="tree-connectors" aria-hidden="true">
        <span className="tree-connectors__stem" />
        <span className="tree-connectors__line" />
        <i className="connector-dot connector-dot--left" />
        <i className="connector-dot connector-dot--center" />
        <i className="connector-dot connector-dot--right" />
      </div>
      <div className={`branches-grid branches-grid--${Math.min(branches.length, 3)}`}>
        {branches.map((branch) => (
          <BranchCard
            key={branch.id}
            branch={branch}
            isSelected={selectedId === branch.id}
            onSelect={onSelect}
            onOpenTree={() => onOpenTree(branch.id)}
          />
        ))}
      </div>
    </section>
  );
}
