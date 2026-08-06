import type { FavoriteTarget } from './types';

const STORAGE_PREFIX = 'riot-titles-attune:favorites:v1:';

type FavoriteStorage = {
  titles?: FavoriteTarget[];
  nodes?: FavoriteTarget[];
};

function storageKey(platform: string, riotId: string): string {
  return `${STORAGE_PREFIX}${platform.toUpperCase()}:${encodeURIComponent(riotId.trim().toLowerCase())}`;
}

export function favoriteTargetKey(target: FavoriteTarget): string {
  return `${target.kind}:${target.titleId}:${target.challengeId ?? ''}`;
}

function sanitize(target: unknown): FavoriteTarget | null {
  if (!target || typeof target !== 'object') return null;
  const candidate = target as Partial<FavoriteTarget>;
  if ((candidate.kind !== 'title' && candidate.kind !== 'node') || typeof candidate.titleId !== 'string' || !candidate.titleId || typeof candidate.label !== 'string' || !candidate.label) return null;
  if (candidate.kind === 'node' && !Number.isInteger(candidate.challengeId)) return null;
  return { kind: candidate.kind, titleId: candidate.titleId, challengeId: candidate.challengeId, label: candidate.label };
}

export function loadFavorites(platform: string, riotId: string): FavoriteTarget[] {
  try {
    const raw = localStorage.getItem(storageKey(platform, riotId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as FavoriteStorage;
    const entries = [...(Array.isArray(parsed.titles) ? parsed.titles : []), ...(Array.isArray(parsed.nodes) ? parsed.nodes : [])]
      .map(sanitize)
      .filter((target): target is FavoriteTarget => target !== null);
    return entries.filter((target, index) => entries.findIndex((item) => favoriteTargetKey(item) === favoriteTargetKey(target)) === index);
  } catch {
    return [];
  }
}

export function saveFavorites(platform: string, riotId: string, favorites: FavoriteTarget[]): void {
  const unique = favorites.filter((target, index) => favorites.findIndex((item) => favoriteTargetKey(item) === favoriteTargetKey(target)) === index);
  const payload: FavoriteStorage = {
    titles: unique.filter((target) => target.kind === 'title'),
    nodes: unique.filter((target) => target.kind === 'node'),
  };
  localStorage.setItem(storageKey(platform, riotId), JSON.stringify(payload));
}

export function toggleFavorite(favorites: FavoriteTarget[], target: FavoriteTarget): FavoriteTarget[] {
  const key = favoriteTargetKey(target);
  const exists = favorites.some((item) => favoriteTargetKey(item) === key);
  return exists ? favorites.filter((item) => favoriteTargetKey(item) !== key) : [...favorites, target];
}

export function hasFavorite(favorites: FavoriteTarget[], target: FavoriteTarget): boolean {
  return favorites.some((item) => favoriteTargetKey(item) === favoriteTargetKey(target));
}
