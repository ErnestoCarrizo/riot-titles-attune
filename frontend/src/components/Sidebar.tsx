import type { Branch } from '../types';
import type { FavoriteTarget } from '../types';
import { Icon } from './Icon';

type Props = { branches: Branch[]; destination: string; progress: number; onNewQuery: () => void; onCollapse: () => void; favorites: FavoriteTarget[]; onOpenFavorite: (favorite: FavoriteTarget) => void };

export function Sidebar({ branches, destination, progress, onNewQuery, onCollapse, favorites, onOpenFavorite }: Props) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <a className="brand__link" href="#top" aria-label="Riot Titles Attune">
          <span className="brand__mark">RT</span>
          <span><strong>RIOT TITLES</strong><small>ATTUNE</small></span>
        </a>
        <button className="sidebar-toggle" type="button" onClick={onCollapse} aria-label="Ocultar barra lateral" aria-expanded="true" title="Ocultar barra lateral"><Icon name="chevron-left" size={17} /></button>
      </div>

      <nav className="sidebar__nav" aria-label="Progreso">
        <p className="eyebrow">Destino</p>
        <a className="sidebar__active" href="#tree">
          <Icon name="diamond" size={19} />
          {destination}
        </a>

        {favorites.length ? <><p className="eyebrow sidebar__section">Fijados</p><div className="sidebar__favorites">{favorites.map((favorite) => <button className="sidebar__favorite" type="button" key={`${favorite.kind}:${favorite.titleId}:${favorite.challengeId ?? ''}`} onClick={() => onOpenFavorite(favorite)} aria-label={`Abrir ${favorite.label}`}><span className="mini-icon mini-icon--gold"><Icon name={favorite.kind === 'title' ? 'diamond' : 'star'} size={15} /></span><span><strong>{favorite.label}</strong><small>{favorite.kind === 'title' ? 'Título' : 'Rama'}</small></span></button>)}</div></> : null}

        <p className="eyebrow sidebar__section">Ramas clave</p>
        <div className="sidebar__branches">
          {branches.map((branch) => (
            <a href={`#${branch.id}`} key={branch.id}>
              <span className={`mini-icon mini-icon--${branch.tone}`}><Icon name={branch.icon} size={17} /></span>
              <span><strong>{branch.name}</strong><small>{branch.progress}%</small></span>
            </a>
          ))}
        </div>

        <p className="eyebrow sidebar__section">Estados</p>
        <ul className="legend">
          <li><i className="legend__dot legend__dot--cyan" />Desbloqueado</li>
          <li><i className="legend__dot legend__dot--orange" />En progreso</li>
          <li><i className="legend__dot legend__dot--muted" />Pendiente</li>
        </ul>
      </nav>

      <div className="sidebar__footer">
        <div className="profile">
          <span className="profile__crest"><Icon name="trophy" size={18} /></span>
          <span><strong>ATTUNE</strong><small>Nivel Maestro</small></span>
        </div>
        <div className="profile__track"><span style={{ width: `${progress}%` }} /></div>
        <button className="back-button" type="button" onClick={onNewQuery}><Icon name="arrow-left" size={18} />Nueva consulta</button>
      </div>
    </aside>
  );
}
