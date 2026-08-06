import { SegmentedControl } from './SegmentedControl';
import { Icon } from './Icon';
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
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
};

export function PageHeader({ view, onViewChange, title, subtitle, onBack, showViewToggle = true, backLabel = 'Dios de ARAM', actions, sidebarCollapsed = false, onToggleSidebar }: Props) {
  return (
    <header className="page-header" id="top">
      <div>
        <p className="breadcrumb">{onBack ? <button className="tree-back-button" type="button" onClick={onBack}>Volver a {backLabel}</button> : null}{onBack ? <span>›</span> : null}Mapa de progreso <span>›</span> Imaginación</p>
        <h1>{title}</h1>
        <p className="page-header__subtitle">{subtitle}</p>
      </div>
      <div className="page-header__actions">
        {sidebarCollapsed && onToggleSidebar ? <button className="sidebar-toggle sidebar-toggle--main" type="button" onClick={onToggleSidebar} aria-label="Mostrar barra lateral" aria-expanded="false" title="Mostrar barra lateral"><Icon name="chevron-right" size={17} /></button> : null}
        {actions}
        {showViewToggle ? <SegmentedControl value={view} onChange={onViewChange} /> : null}
      </div>
    </header>
  );
}
