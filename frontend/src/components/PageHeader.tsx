import { SegmentedControl } from './SegmentedControl';
import type { ReactNode } from 'react';

type Props = {
  view: 'tree' | 'list';
  onViewChange: (value: 'tree' | 'list') => void;
  title: string;
  subtitle: string;
  onBack?: () => void;
  showViewToggle?: boolean;
  backLabel?: string;
  actions?: ReactNode;
};

export function PageHeader({ view, onViewChange, title, subtitle, onBack, showViewToggle = true, backLabel = 'Dios de ARAM', actions }: Props) {
  return (
    <header className="page-header" id="top">
      <div>
        <p className="breadcrumb">{onBack ? <button className="tree-back-button" type="button" onClick={onBack}>Volver a {backLabel}</button> : null}{onBack ? <span>›</span> : null}Mapa de progreso <span>›</span> Imaginación</p>
        <h1>{title}</h1>
        <p className="page-header__subtitle">{subtitle}</p>
      </div>
      <div className="page-header__actions">
        {actions}
        {showViewToggle ? <SegmentedControl value={view} onChange={onViewChange} /> : null}
      </div>
    </header>
  );
}
