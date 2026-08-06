import type { FormEvent } from 'react';
import { Icon } from './Icon';
import { ProgressBar } from './ProgressBar';
import type { ProgressResponse, TitleProgress, TreeNode, TreeResponse } from '../types';

type Platform = { code: string; name: string };

type FormProps = {
  riotId: string;
  platform: string;
  platforms: Platform[];
  loading: boolean;
  error: string;
  onRiotIdChange: (value: string) => void;
  onPlatformChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

type PanelProps = {
  primary: ProgressResponse;
  secondary: ProgressResponse;
  selectedTitleId: string | null;
  activeNodeId: string | null;
  primaryTree: TreeResponse | null;
  secondaryTree: TreeResponse | null;
  treeLoading: boolean;
  onSelectTitle: (titleId: string) => void;
  onAdvanceNode: (nodeId: string) => void;
  onClose: () => void;
};

function titlePercent(title: TitleProgress | undefined): number | null {
  if (!title || title.progressPercent === null) return null;
  return Math.round(title.progressPercent);
}

function statusLabel(status: TitleProgress['status'] | TreeNode['status'] | undefined): string {
  return status ? ({ unlocked: 'Desbloqueado', in_progress: 'En progreso', not_started: 'Sin comenzar', unknown: 'No calculable' })[status] : 'Sin datos';
}

function nodePercent(node: TreeNode | undefined): number | null {
  if (!node || node.progressPercent === null) return null;
  return Math.round(node.progressPercent);
}

function findTreeNode(nodes: TreeNode[], id: string): TreeNode | undefined {
  for (const node of nodes) {
    if (String(node.challengeId) === id) return node;
    const nested = findTreeNode(node.children, id);
    if (nested) return nested;
  }
  return undefined;
}

function Score({ percent, status, tone, owner }: { percent: number | null; status: TitleProgress['status'] | TreeNode['status'] | undefined; tone: 'cyan' | 'orange'; owner: string }) {
  return (
    <div className="comparison-score">
      <div><strong>{percent === null ? '—' : `${percent}%`}</strong><small>{statusLabel(status)}</small></div>
      <ProgressBar value={percent ?? 0} tone={tone} label={`Progreso de ${owner}`} />
    </div>
  );
}

function differenceLabel(primaryPercent: number | null, secondaryPercent: number | null, owner: string): string {
  if (primaryPercent === null || secondaryPercent === null) return 'Sin diferencia calculable';
  const difference = primaryPercent - secondaryPercent;
  return `${difference >= 0 ? '+' : ''}${difference} puntos para ${owner}`;
}

function titleTooltip(title: TitleProgress): string {
  const descriptions = title.requirements.map((requirement) => requirement.challengeDescription).filter(Boolean);
  return descriptions.join(' ') || `Completá los objetivos de ${title.titleName}.`;
}

export function ComparisonForm({ riotId, platform, platforms, loading, error, onRiotIdChange, onPlatformChange, onSubmit }: FormProps) {
  return (
    <form className="comparison-form" onSubmit={onSubmit}>
      <div className="comparison-form__heading">
        <div><p className="eyebrow eyebrow--gold">Nueva comparación</p><h2>Cargar otro jugador</h2></div>
        <span className="muted">El perfil actual se conserva</span>
      </div>
      <label>Riot ID<input value={riotId} onChange={(event) => onRiotIdChange(event.target.value)} placeholder="Nombre#TAG" autoComplete="off" required /><small>Usá el nombre y tag del segundo jugador.</small></label>
      <label>Servidor<select value={platform} onChange={(event) => onPlatformChange(event.target.value)} required>{platforms.map((item) => <option key={item.code} value={item.code}>{item.code} · {item.name}</option>)}</select></label>
      <button className="comparison-form__submit" type="submit" disabled={loading}>{loading ? 'Consultando…' : 'Comparar'} <Icon name="compare" size={17} /></button>
      {error ? <p className="comparison-form__error" role="alert">{error}</p> : null}
    </form>
  );
}

export function ComparisonPanel({ primary, secondary, selectedTitleId, activeNodeId, primaryTree, secondaryTree, treeLoading, onSelectTitle, onAdvanceNode, onClose }: PanelProps) {
  const secondaryTitles = new Map(secondary.titles.map((title) => [title.titleId, title]));
  const overallPrimary = Math.round(primary.summary.completionPercentage);
  const overallSecondary = Math.round(secondary.summary.completionPercentage);
  const focusedTitle = selectedTitleId ? primary.titles.find((title) => title.titleId === selectedTitleId) : undefined;
  const focusedSecondaryTitle = selectedTitleId ? secondaryTitles.get(selectedTitleId) : undefined;
  const focusedNode = activeNodeId && primaryTree ? findTreeNode(primaryTree.roots, activeNodeId) : undefined;
  const focusedTreeReady = Boolean(selectedTitleId && primaryTree?.titleId === selectedTitleId && secondaryTree?.titleId === selectedTitleId);
  const nodeRows = focusedTreeReady ? (focusedNode ? focusedNode.children : primaryTree?.roots || []) : [];
  const contextual = Boolean(selectedTitleId);
  const contextName = focusedNode?.challengeName || focusedTitle?.titleName || 'título seleccionado';

  return (
    <section className="comparison-panel" aria-labelledby="comparison-title">
      <div className="comparison-panel__heading">
        <div><p className="eyebrow eyebrow--gold">Comparación activa</p><h2 id="comparison-title">{contextual ? `Comparando ${focusedTitle?.titleName || 'título'}` : 'Progreso lado a lado'}</h2><p>{contextual ? `Mismo título y nivel: ${contextName}. El chevrón avanza al siguiente conjunto de hijos cuando existe.` : 'Elegí un título para volver a explorarlo en el árbol del perfil principal.'}</p></div>
        <button className="comparison-close" type="button" onClick={onClose} aria-label="Cerrar comparación">×</button>
      </div>
      <div className="comparison-players">
        <div className="comparison-player comparison-player--primary"><span className="comparison-player__mark">{primary.player.gameName.slice(0, 1).toUpperCase()}</span><div><strong>{primary.player.gameName}</strong><small>Perfil principal · {overallPrimary}% total</small></div></div>
        <span className="comparison-vs">VS</span>
        <div className="comparison-player comparison-player--secondary"><span className="comparison-player__mark">{secondary.player.gameName.slice(0, 1).toUpperCase()}</span><div><strong>{secondary.player.gameName}</strong><small>Perfil comparado · {overallSecondary}% total</small></div></div>
      </div>
      {contextual && treeLoading ? <p className="comparison-empty">Cargando el mismo árbol para ambos perfiles…</p> : null}
      {contextual && focusedTreeReady && nodeRows.length ? <div className="comparison-context-label">Dependencias de {contextName}</div> : null}
      <div className="comparison-list" role="list" aria-label={contextual ? 'Comparación de nodos' : 'Comparación de títulos'}>
        {!contextual ? primary.titles.map((title) => {
          const other = secondaryTitles.get(title.titleId);
          const primaryPercent = titlePercent(title);
          const secondaryPercent = titlePercent(other);
          return <button className={`comparison-row ${selectedTitleId === title.titleId ? 'is-selected' : ''}`} type="button" role="listitem" key={title.titleId} onClick={() => onSelectTitle(title.titleId)}><span className="comparison-row__title comparison-row__title--tooltip" data-tooltip={titleTooltip(title)} title={titleTooltip(title)}><strong>{title.titleName}</strong><small>{differenceLabel(primaryPercent, secondaryPercent, primary.player.gameName)}</small></span><Score percent={primaryPercent} status={title.status} tone="cyan" owner={primary.player.gameName} /><Score percent={secondaryPercent} status={other?.status} tone="orange" owner={secondary.player.gameName} /><Icon name="chevron-right" size={17} /></button>;
        }) : focusedTreeReady && nodeRows.length ? nodeRows.map((node) => {
          const other = secondaryTree ? findTreeNode(secondaryTree.roots, String(node.challengeId)) : undefined;
          const primaryPercent = nodePercent(node);
          const secondaryPercent = nodePercent(other);
          const canAdvance = node.children.length > 0;
          const tooltip = node.challengeDescription || `Completá ${node.challengeName} para alcanzar ${node.targetTier}.`;
          return <button className={`comparison-row comparison-row--node ${canAdvance ? '' : 'comparison-row--leaf'}`} type="button" role="listitem" key={node.challengeId} onClick={() => { if (canAdvance) onAdvanceNode(String(node.challengeId)); }} aria-label={`${node.challengeName}. ${canAdvance ? 'Avanzar a sus hijos' : 'Objetivo final'}`}><span className="comparison-row__title comparison-row__title--tooltip" data-tooltip={tooltip} title={tooltip}><strong>{node.challengeName}</strong><small>{differenceLabel(primaryPercent, secondaryPercent, primary.player.gameName)}</small></span><Score percent={primaryPercent} status={node.status} tone="cyan" owner={primary.player.gameName} /><Score percent={secondaryPercent} status={other?.status} tone="orange" owner={secondary.player.gameName} />{canAdvance ? <Icon name="chevron-right" size={17} /> : <span aria-hidden="true" />}</button>;
        }) : contextual && !treeLoading && focusedTitle ? <button className="comparison-row is-selected" type="button" role="listitem" onClick={() => onSelectTitle(focusedTitle.titleId)}><span className="comparison-row__title comparison-row__title--tooltip" data-tooltip={titleTooltip(focusedTitle)} title={titleTooltip(focusedTitle)}><strong>{focusedTitle.titleName}</strong><small>{differenceLabel(titlePercent(focusedTitle), titlePercent(focusedSecondaryTitle), primary.player.gameName)}</small></span><Score percent={titlePercent(focusedTitle)} status={focusedTitle.status} tone="cyan" owner={primary.player.gameName} /><Score percent={titlePercent(focusedSecondaryTitle)} status={focusedSecondaryTitle?.status} tone="orange" owner={secondary.player.gameName} /><span aria-hidden="true" /></button> : null}
      </div>
    </section>
  );
}
