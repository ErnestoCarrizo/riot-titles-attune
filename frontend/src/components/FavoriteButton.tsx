import { Icon } from './Icon';

type Props = {
  isFavorite: boolean;
  label: string;
  onToggle: () => void;
  className?: string;
};

export function FavoriteButton({ isFavorite, label, onToggle, className = '' }: Props) {
  const action = isFavorite ? `Quitar ${label} de fijados` : `Fijar ${label}`;
  return <button className={`favorite-button ${isFavorite ? 'is-active' : ''} ${className}`} type="button" onClick={onToggle} aria-label={action} aria-pressed={isFavorite} title={action}><Icon name="star" size={18} /></button>;
}
