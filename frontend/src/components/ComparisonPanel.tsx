import type { FormEvent } from 'react';
import { Icon } from './Icon';
import { ProgressBar } from './ProgressBar';
import type { ProgressResponse, TitleProgress } from '../types';

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
  onSelectTitle: (titleId: string) => void;
  onClose: () => void;
};

function titlePercent(title: TitleProgress | undefined): number | null {
  if (!title || title.progressPercent === null) return null;
  return Math.round(title.progressPercent);
}

function statusLabel(status: TitleProgress['status']): string {
  return ({ unlocked: 'Desbloqueado', in_progress: 'En progreso', not_started: 'Sin comenzar', unknown: 'No calculable' })[status];
}

function Score({ title, tone, owner }: { title: TitleProgress | undefined; tone: 'cyan' | 'orange'; owner: string }) {
  const percent = titlePercent(title);
  return (
    <div className="comparison-score">
      <div><strong>{percent === null ? '—' : `${percent}%`}</strong><small>{title ? statusLabel(title.status) : 'Sin datos'}</small></div>
      <ProgressBar value={percent ?? 0} tone={tone} label={`Progreso de ${owner}`} />
    </div>
  );
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

export function ComparisonPanel({ primary, secondary, selectedTitleId, onSelectTitle, onClose }: PanelProps) {
  const secondaryTitles = new Map(secondary.titles.map((title) => [title.titleId, title]));
  const overallPrimary = Math.round(primary.summary.completionPercentage);
  const overallSecondary = Math.round(secondary.summary.completionPercentage);

  return (
    <section className="comparison-panel" aria-labelledby="comparison-title">
      <div className="comparison-panel__heading">
        <div><p className="eyebrow eyebrow--gold">Comparación activa</p><h2 id="comparison-title">Progreso lado a lado</h2><p>Elegí un título para volver a explorarlo en el árbol del perfil principal.</p></div>
        <button className="comparison-close" type="button" onClick={onClose} aria-label="Cerrar comparación">×</button>
      </div>
      <div className="comparison-players">
        <div className="comparison-player comparison-player--primary"><span className="comparison-player__mark">{primary.player.gameName.slice(0, 1).toUpperCase()}</span><div><strong>{primary.player.gameName}</strong><small>Perfil principal · {overallPrimary}% total</small></div></div>
        <span className="comparison-vs">VS</span>
        <div className="comparison-player comparison-player--secondary"><span className="comparison-player__mark">{secondary.player.gameName.slice(0, 1).toUpperCase()}</span><div><strong>{secondary.player.gameName}</strong><small>Perfil comparado · {overallSecondary}% total</small></div></div>
      </div>
      <div className="comparison-list" role="list" aria-label="Comparación de títulos">
        {primary.titles.map((title) => {
          const other = secondaryTitles.get(title.titleId);
          const primaryPercent = titlePercent(title);
          const secondaryPercent = titlePercent(other);
          const difference = primaryPercent !== null && secondaryPercent !== null ? primaryPercent - secondaryPercent : null;
          return (
            <button className={`comparison-row ${selectedTitleId === title.titleId ? 'is-selected' : ''}`} type="button" role="listitem" key={title.titleId} onClick={() => onSelectTitle(title.titleId)}>
              <span className="comparison-row__title"><strong>{title.titleName}</strong><small>{difference === null ? 'Sin diferencia calculable' : `${difference >= 0 ? '+' : ''}${difference} puntos para ${primary.player.gameName}`}</small></span>
              <Score title={title} tone="cyan" owner={primary.player.gameName} />
              <Score title={other} tone="orange" owner={secondary.player.gameName} />
              <Icon name="chevron-right" size={17} />
            </button>
          );
        })}
      </div>
    </section>
  );
}
