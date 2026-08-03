import { FormEvent, useEffect, useMemo, useState } from 'react';
import { BranchCard } from './components/BranchCard';
import { DetailPanel } from './components/DetailPanel';
import { Icon } from './components/Icon';
import { PageHeader } from './components/PageHeader';
import { ProgressSummary } from './components/ProgressSummary';
import { Sidebar } from './components/Sidebar';
import { SkillTree } from './components/SkillTree';
import { ProgressBar } from './components/ProgressBar';
import type { Branch, ProgressResponse, Requirement, TitleProgress, TreeNode, TreeResponse } from './types';

const iconNames = ['sword', 'leaf', 'trophy'] as const;
const tones = ['cyan', 'orange', 'lime'] as const;

function titleProgress(title: TitleProgress, requirement: Requirement): number {
  if (title.status === 'unlocked') return 100;
  if (requirement.currentValue !== null && requirement.targetValue && requirement.targetValue > 0) {
    return Math.max(0, Math.min(100, Math.round(requirement.currentValue / requirement.targetValue * 100)));
  }
  return Math.round(title.progressPercent ?? 0);
}

function branchStatus(title: TitleProgress, progress: number): Branch['status'] {
  if (title.status === 'unlocked' || progress >= 100) return 'unlocked';
  if (title.status === 'in_progress' || progress > 0) return 'in-progress';
  return 'pending';
}

function toBranches(title: TitleProgress): Branch[] {
  return title.requirements.slice(0, 3).map((requirement, index) => {
    const progress = titleProgress(title, requirement);
    return {
      id: String(requirement.challengeId),
      name: requirement.challengeName,
      rank: `Rango ${requirement.targetTier}`,
      progress,
      tone: tones[index % tones.length],
      icon: iconNames[index % iconNames.length],
      status: branchStatus(title, progress),
      description: requirement.challengeDescription,
      hasChildren: true,
      currentValue: requirement.currentValue,
      targetValue: requirement.targetValue,
      remainingValue: requirement.remainingValue,
    };
  });
}

function branchesFromTreeNode(treeNode: TreeNode): Branch[] {
  return treeNode.children.map((child, index) => {
    const progress = Math.round(child.progressPercent ?? 0);
    return {
      id: String(child.challengeId),
      name: child.challengeName,
      rank: `Rango ${child.targetTier}`,
      progress,
      tone: tones[index % tones.length],
      icon: iconNames[index % iconNames.length],
      status: child.status === 'unlocked' || progress >= 100 ? 'unlocked' : child.status === 'in_progress' || progress > 0 ? 'in-progress' : 'pending',
      description: child.challengeDescription,
      hasChildren: child.children.length > 0,
      currentValue: child.currentValue,
      targetValue: child.targetValue,
      remainingValue: child.remainingValue,
    };
  });
}

function featuredTitle(data: ProgressResponse): TitleProgress | undefined {
  return data.titles.find((title) => title.titleName.toLocaleLowerCase().includes('dios de aram'))
    ?? data.titles.find((title) => title.requirements.length >= 3)
    ?? data.titles[0];
}

function statusLabel(status: TreeNode['status']): string {
  return ({ unlocked: 'Desbloqueado', in_progress: 'En progreso', not_started: 'Sin comenzar', unknown: 'No calculable' })[status];
}

function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return Number.isInteger(value) ? String(value) : value.toLocaleString('es-AR', { maximumFractionDigits: 2 });
}

function metricLabel(current: number | null, target: number | null, remaining: number | null): string {
  if (target === null) return 'Cantidad no calculable';
  const remainingLabel = remaining === null ? '' : ` · faltan ${formatValue(Math.max(0, remaining))}`;
  return `${formatValue(current)} / ${formatValue(target)}${remainingLabel}`;
}

function findTreeNode(nodes: TreeNode[], id: string): TreeNode | undefined {
  for (const node of nodes) {
    if (String(node.challengeId) === id) return node;
    const nested = findTreeNode(node.children, id);
    if (nested) return nested;
  }
  return undefined;
}

type MapSelection = {
  id: string;
  name: string;
  description: string;
  status: TreeNode['status'];
  progressPercent: number | null;
  currentTier: string;
  targetTier: string;
  currentValue: number | null;
  targetValue: number | null;
  remainingText: string;
  children: TreeNode[];
};

function selectionFromNode(treeNode: TreeNode): MapSelection {
  return {
    id: String(treeNode.challengeId),
    name: treeNode.challengeName,
    description: treeNode.challengeDescription,
    status: treeNode.status,
    progressPercent: treeNode.progressPercent,
    currentTier: treeNode.currentTier,
    targetTier: treeNode.targetTier,
    currentValue: treeNode.currentValue,
    targetValue: treeNode.targetValue,
    remainingText: treeNode.remainingText,
    children: treeNode.children,
  };
}

function selectionFromTree(tree: TreeResponse): MapSelection {
  const firstRoot = tree.roots[0];
  return {
    id: `title-${tree.titleId}`,
    name: tree.titleName,
    description: 'El título raíz y sus dependencias directas. Seleccioná un nodo para explorar su siguiente nivel.',
    status: tree.status,
    progressPercent: tree.progressPercent,
    currentTier: firstRoot?.currentTier || 'NONE',
    targetTier: firstRoot?.targetTier || 'MASTER',
    currentValue: null,
    targetValue: null,
    remainingText: 'Completá las dependencias directas para alcanzar el rango requerido.',
    children: tree.roots,
  };
}

function DependencyMapNode({ treeNode, selectedId, onSelect }: { treeNode: TreeNode; selectedId: string; onSelect: (node: TreeNode) => void }) {
  const progress = treeNode.progressPercent === null ? 0 : Math.round(treeNode.progressPercent);
  return (
    <div className={`dependency-map-branch dependency-map-branch--${treeNode.status}`}>
      <button className={`dependency-map-node ${selectedId === String(treeNode.challengeId) ? 'is-selected' : ''}`} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => onSelect(treeNode)}>
        <span className="dependency-map-node__icon">{treeNode.isCapstone ? '✦' : '◇'}</span>
        <strong>{treeNode.challengeName}</strong>
        {treeNode.isCapstone ? <span className="dependency-map-node__tag">Capstone</span> : null}
        <small>{statusLabel(treeNode.status)} · {treeNode.targetTier}</small>
        <span className="dependency-map-node__progress">{progress}%</span>
        <span className="dependency-map-node__count">{metricLabel(treeNode.currentValue, treeNode.targetValue, treeNode.remainingValue)}</span>
        <span className="dependency-map-node__track"><span style={{ width: `${progress}%` }} /></span>
      </button>
      {treeNode.children.length ? <div className="dependency-map-children">{treeNode.children.map((child) => <DependencyMapNode key={child.challengeId} treeNode={child} selectedId={selectedId} onSelect={onSelect} />)}</div> : null}
    </div>
  );
}

function DependencyDetailPanel({ selected }: { selected: MapSelection }) {
  const progress = selected.progressPercent === null ? 0 : Math.round(selected.progressPercent);
  return (
    <section className="dependency-selected-panel" aria-labelledby="selected-dependency-title">
      <div className="dependency-selected-intro">
        <p className="eyebrow eyebrow--gold">Nodo seleccionado</p>
        <h2 id="selected-dependency-title">{selected.name}</h2>
        <span className="rank-pill">Rango {selected.targetTier}</span>
        <p>{selected.description}</p>
        <div className="dependency-selected-progress"><strong>{progress}%</strong><ProgressBar value={progress} tone={selected.status === 'in_progress' ? 'orange' : 'cyan'} label={`Progreso de ${selected.name}`} /><small>{selected.currentTier} · objetivo {selected.targetTier} · {selected.currentValue ?? '—'} / {selected.targetValue ?? '—'}</small><span>{selected.remainingText}</span></div>
      </div>
      <div className="dependency-selected-divider"><span>›</span></div>
      <div className="dependency-selected-objectives">
        <p className="eyebrow eyebrow--gold">Dependencias directas</p>
        <div className="dependency-selected-list">
          {selected.children.length ? selected.children.map((child) => {
            const childProgress = child.progressPercent === null ? 0 : Math.round(child.progressPercent);
            const tooltip = child.challengeDescription || `Completá ${child.challengeName} para alcanzar ${child.targetTier}.`;
            return <button className="dependency-selected-row dependency-selected-row--tooltip" type="button" key={child.challengeId} title={tooltip} data-tooltip={tooltip} aria-label={`${child.challengeName}. ${tooltip}`}><span className="dependency-selected-icon">{child.isCapstone ? '✦' : '◇'}</span><span className="dependency-selected-copy"><strong>{child.challengeName}</strong><small>{child.currentTier} · objetivo {child.targetTier}</small><em>{metricLabel(child.currentValue, child.targetValue, child.remainingValue)}</em></span><ProgressBar value={childProgress} tone={child.status === 'in_progress' ? 'orange' : 'cyan'} label={`Progreso de ${child.challengeName}`} /><b>{childProgress}%</b><span className={`dependency-selected-status dependency-selected-status--${child.status}`}>{child.status === 'unlocked' ? '✓' : '○'}</span></button>;
          }) : <p className="dependency-selected-empty">Este nodo no tiene objetivos hijos.</p>}
        </div>
      </div>
    </section>
  );
}

function TreeDialog({ tree, onClose }: { tree: TreeResponse; onClose: () => void }) {
  const [selected, setSelected] = useState<MapSelection>(() => selectionFromTree(tree));
  const rootSelection = selectionFromTree(tree);
  return (
    <div className="tree-dialog-backdrop" role="presentation" onClick={onClose}>
      <section className="tree-dialog-panel dependency-dialog-panel" role="dialog" aria-modal="true" aria-labelledby="tree-dialog-title" onClick={(event) => event.stopPropagation()}>
        <div className="tree-dialog-heading">
          <div><p className="eyebrow eyebrow--gold">Mapa de dependencias</p><h2 id="tree-dialog-title">{tree.titleName}</h2><p className="muted">{statusLabel(tree.status)} · {tree.roots.length} nodo{tree.roots.length === 1 ? '' : 's'} principal{tree.roots.length === 1 ? '' : 'es'}</p></div>
          <button className="close-button" type="button" onClick={onClose} aria-label="Cerrar desglose">×</button>
        </div>
        <div className="dependency-map-scroll">
          <div className="dependency-map">
            <button className={`dependency-map-root ${selected.id === rootSelection.id ? 'is-selected' : ''}`} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => setSelected(rootSelection)}>
              <span className="dependency-map-root__icon">✦</span><strong>{tree.titleName}</strong><span>Rango {rootSelection.targetTier}</span><b>{Math.round(tree.progressPercent ?? 0)}%</b>
            </button>
            <div className={`dependency-map-roots dependency-map-roots--${Math.min(tree.roots.length, 3)}`}>
              {tree.roots.map((root) => <DependencyMapNode key={root.challengeId} treeNode={root} selectedId={selected.id} onSelect={(node) => setSelected(selectionFromNode(node))} />)}
            </div>
          </div>
        </div>
        <DependencyDetailPanel selected={selected} />
      </section>
    </div>
  );
}

function CatalogSection({ titles, onOpenTree }: { titles: TitleProgress[]; onOpenTree: (titleId: string) => void }) {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<'all' | TitleProgress['status']>('all');
  const visible = titles.filter((title) => {
    const matchesFilter = filter === 'all' || title.status === filter;
    const text = `${title.titleName} ${title.requirements.map((requirement) => requirement.challengeName).join(' ')}`.toLocaleLowerCase();
    return matchesFilter && text.includes(query.toLocaleLowerCase());
  });
  const labels: Record<'all' | TitleProgress['status'], string> = { all: 'Todos', unlocked: 'Desbloqueados', in_progress: 'En progreso', not_started: 'Sin comenzar', unknown: 'No calculable' };
  return (
    <section className="catalog-panel" aria-labelledby="catalog-title">
      <div className="catalog-heading"><div><p className="eyebrow eyebrow--gold">Catálogo personal</p><h2 id="catalog-title">Tus títulos</h2></div><span className="muted">{visible.length} de {titles.length}</span></div>
      <div className="catalog-tools"><label><span className="sr-only">Buscar títulos</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar título o desafío" /></label><div className="catalog-filters">{Object.keys(labels).map((key) => <button key={key} type="button" className={filter === key ? 'is-active' : ''} onClick={() => setFilter(key as typeof filter)}>{labels[key as keyof typeof labels]}</button>)}</div></div>
      <div className="catalog-list">{visible.map((title) => <article className="catalog-card" key={title.titleId}><div><h3>{title.titleName}</h3><span className={`title-status status-${title.status}`}>{labels[title.status]}</span></div><div className="catalog-card__progress"><span>{title.progressPercent === null ? 'Progreso no calculable' : `${Math.round(title.progressPercent)}% de avance`}</span>{title.progressPercent !== null ? <ProgressBar value={title.progressPercent} tone={title.status === 'in_progress' ? 'orange' : 'cyan'} /> : null}</div><button type="button" onClick={() => onOpenTree(title.titleId)}>Ver desglose <Icon name="chevron-right" size={15} /></button></article>)}</div>
      {!visible.length ? <p className="catalog-empty">No hay títulos que coincidan con esta búsqueda.</p> : null}
    </section>
  );
}

function CatalogHome({ data, onSelectTitle, onNewQuery }: { data: ProgressResponse; onSelectTitle: (titleId: string) => void; onNewQuery: () => void }) {
  return (
    <div className="app-shell" id="top">
      <Sidebar branches={[]} destination="Catalogo" progress={data.summary.completionPercentage} onNewQuery={onNewQuery} />
      <main className="main-content">
        <PageHeader view="list" onViewChange={() => undefined} title="Tus titulos" subtitle="Elegi un titulo para explorar su arbol de progreso y sus objetivos." showViewToggle={false} />
        <ProgressSummary progress={Math.round(data.summary.completionPercentage)} branchCount={data.titles.length} challengeCount={data.titles.reduce((total, title) => total + title.requirements.length, 0)} />
        <CatalogSection titles={data.titles} onOpenTree={onSelectTitle} />
      </main>
    </div>
  );
}

function QueryScreen({ riotId, platform, platforms, loading, error, onRiotIdChange, onPlatformChange, onSubmit }: {
  riotId: string;
  platform: string;
  platforms: { code: string; name: string }[];
  loading: boolean;
  error: string;
  onRiotIdChange: (value: string) => void;
  onPlatformChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
}) {
  return (
    <main className="query-screen">
      <div className="query-screen__brand"><span className="brand__mark">RT</span><span><strong>RIOT TITLES</strong><small>ATTUNE</small></span></div>
      <div className="query-screen__copy"><p className="breadcrumb">Mapa de progreso <span>›</span> Imaginación</p><h1>Todos tus títulos, en un solo lugar.</h1><p>Ingresá tu Riot ID para entender qué títulos ya ganaste y cuál es el próximo que está al alcance.</p></div>
      <form className="query-screen__form" onSubmit={onSubmit}>
        <div className="query-screen__form-heading"><div><p className="eyebrow eyebrow--gold">Consulta</p><h2>Buscá tu cuenta</h2></div><span className="query-live"><i /> Datos en vivo</span></div>
        <label>Riot ID<input value={riotId} onChange={(event) => onRiotIdChange(event.target.value)} placeholder="Nombre#TAG" autoComplete="off" required /><small>Usá el nombre y el tag con los que jugás actualmente.</small></label>
        <label>Servidor<select value={platform} onChange={(event) => onPlatformChange(event.target.value)} required>{platforms.map((item) => <option key={item.code} value={item.code}>{item.code} · {item.name}</option>)}</select></label>
        <button className="query-screen__submit" type="submit" disabled={loading}>{loading ? 'Consultando…' : 'Consultar progreso'} <span>→</span></button>
        {error ? <p className="query-screen__error" role="alert">{error}</p> : null}
      </form>
    </main>
  );
}

export function App() {
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [platforms, setPlatforms] = useState<{ code: string; name: string }[]>([]);
  const [riotId, setRiotId] = useState(localStorage.getItem('riot-id') || '');
  const [platform, setPlatform] = useState(localStorage.getItem('riot-platform') || 'LA2');
  const [view, setView] = useState<'tree' | 'list'>('tree');
  const [selectedTitleId, setSelectedTitleId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tree, setTree] = useState<TreeResponse | null>(null);
  const [activeNode, setActiveNode] = useState<TreeNode | null>(null);

  const featured = data?.titles.find((title) => title.titleId === selectedTitleId);
  const branches = useMemo(() => activeNode ? branchesFromTreeNode(activeNode) : featured ? toBranches(featured) : [], [activeNode, featured]);
  const selectedBranch = branches.find((branch) => branch.id === selectedId) || branches[0];
  const progress = Math.round(activeNode?.progressPercent ?? featured?.progressPercent ?? data?.summary.completionPercentage ?? 0);
  const displayTitle = activeNode?.challengeName || featured?.titleName || 'Tu progreso';
  const displayRank = `Rango ${activeNode?.targetTier || featured?.requirements[0]?.targetTier || 'Maestro'}`;
  const displayDescription = activeNode?.challengeDescription || 'Alcanzá el rango requerido y completá sus dependencias directas.';

  useEffect(() => {
    fetch('/api/platforms').then((response) => response.json()).then((items) => {
      setPlatforms(items);
      if (!items.some((item: { code: string }) => item.code === platform)) setPlatform(items[0]?.code || 'LA2');
    }).catch(() => setError('No se pudieron cargar los servidores.'));
  }, [platform]);

  async function submitQuery(event: FormEvent) {
    event.preventDefault();
    if (!riotId.trim().includes('#')) { setError('Ingresá un Riot ID válido con el formato Nombre#TAG.'); return; }
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/title-progress?riot_id=${encodeURIComponent(riotId.trim())}&platform=${encodeURIComponent(platform)}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'No pudimos completar la consulta.');
      localStorage.setItem('riot-id', riotId.trim());
      localStorage.setItem('riot-platform', platform);
      setData(payload);
      setActiveNode(null);
      setSelectedTitleId(null);
      setSelectedId('');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No pudimos completar la consulta.');
    } finally {
      setLoading(false);
    }
  }

  async function requestTree(titleId: string): Promise<TreeResponse> {
    if (!data) throw new Error('No hay una consulta activa.');
    const response = await fetch(`/api/title-tree?riot_id=${encodeURIComponent(data.player.riotId)}&platform=${encodeURIComponent(data.player.platform)}&title_id=${encodeURIComponent(titleId)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'No pudimos cargar el desglose.');
    return payload;
  }

  function selectTitle(titleId: string) {
    setSelectedTitleId(titleId);
    setActiveNode(null);
    const title = data?.titles.find((item) => item.titleId === titleId);
    setSelectedId(title?.requirements[0] ? String(title.requirements[0].challengeId) : '');
    setView('tree');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function openTree(titleId = featured?.titleId) {
    if (!titleId || !data) return;
    try {
      setTree(await requestTree(titleId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No pudimos cargar el desglose.');
    }
  }

  async function openNode(titleId: string, nodeId: string) {
    try {
      const payload = await requestTree(titleId);
      const target = findTreeNode(payload.roots, nodeId);
      if (!target) throw new Error('No pudimos encontrar ese nodo en el árbol.');
      setTree(null);
      setActiveNode(target);
      setSelectedId(target.children[0] ? String(target.children[0].challengeId) : '');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No pudimos abrir esa rama.');
    }
  }

  if (!data) return <QueryScreen riotId={riotId} platform={platform} platforms={platforms} loading={loading} error={error} onRiotIdChange={setRiotId} onPlatformChange={setPlatform} onSubmit={submitQuery} />;
  if (!featured) return <CatalogHome data={data} onSelectTitle={selectTitle} onNewQuery={() => { setData(null); setActiveNode(null); setSelectedTitleId(null); }} />;

  return (
    <div className="app-shell" id="top">
      <Sidebar branches={branches} destination={featured.titleName} progress={activeNode?.progressPercent ?? featured.progressPercent ?? 0} onNewQuery={() => { setData(null); setActiveNode(null); setSelectedTitleId(null); }} />
      <main className="main-content">
        <PageHeader view={view} onViewChange={setView} title={displayTitle} subtitle={displayDescription} onBack={activeNode ? () => { setActiveNode(null); setSelectedId(featured.requirements[0] ? String(featured.requirements[0].challengeId) : ''); } : undefined} backLabel={featured.titleName} />
        <ProgressSummary progress={progress} branchCount={branches.length} challengeCount={activeNode?.children.length ?? featured.requirements.length} />
        {view === 'tree' ? <SkillTree branches={branches} selectedId={selectedId} onSelect={setSelectedId} title={displayTitle} progress={progress} rank={displayRank} onOpenTree={(nodeId) => openNode(featured.titleId, nodeId)} /> : <section className="list-view" aria-label="Lista de ramas">{branches.map((branch) => <BranchCard key={branch.id} branch={branch} isSelected={selectedId === branch.id} onSelect={setSelectedId} onOpenTree={() => openNode(featured.titleId, branch.id)} />)}</section>}
        <DetailPanel title={activeNode?.challengeName || selectedBranch?.name || featured.titleName} rank={activeNode ? displayRank : selectedBranch?.rank || displayRank} description={activeNode?.challengeDescription || selectedBranch?.description || 'El título máximo de la rama ARAM. Completá sus dependencias directas para alcanzar el rango requerido.'} branches={branches} />
        <p className="footer-note"><Icon name="info" size={17} />Completá las ramas al rango requerido para desbloquear “{featured.titleName}”.</p>
        <CatalogSection titles={data.titles} onOpenTree={selectTitle} />
      </main>
    </div>
  );
}
