import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.cache import LockedMemoryCache
from app.clients.community_dragon import CommunityDragonClient
from app.errors import CatalogUnavailableError, ExternalSchemaError
from app.routing import TIER_ORDER
from app.utils import normalize_search

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CatalogRequirement:
    challenge_id: int
    challenge_name: str
    challenge_description: str
    target_tier: str
    target_value: float | int | None
    reverse_direction: bool
    icon_url: str | None
    progress_start_value: float | int | None = None


@dataclass(frozen=True)
class CatalogTitle:
    title_id: str
    title_name: str
    requirements: tuple[CatalogRequirement, ...]


@dataclass(frozen=True)
class CatalogChallenge:
    challenge_id: int
    challenge_name: str
    challenge_description: str
    parent_challenge_id: int | None
    is_capstone: bool
    is_category: bool
    max_requirement: CatalogRequirement


@dataclass(frozen=True)
class CatalogSnapshot:
    titles: tuple[CatalogTitle, ...]
    locale: str
    fetched_at: datetime
    challenge_graph: dict[int, CatalogChallenge] = field(default_factory=dict)


def _as_records(root: Any, keys: tuple[str, ...], source: str) -> list[dict[str, Any]]:
    if isinstance(root, list):
        records = root
    elif isinstance(root, dict):
        records = None
        for key in keys:
            candidate = root.get(key)
            if isinstance(candidate, list):
                records = candidate
                break
            if isinstance(candidate, dict) and all(isinstance(value, dict) for value in candidate.values()):
                records = [{"id": item_id, **value} for item_id, value in candidate.items()]
                break
        if records is None and all(isinstance(value, dict) for value in root.values()):
            records = [{"id": key, **value} for key, value in root.items()]
    else:
        records = None
    if records is None or any(not isinstance(item, dict) for item in records):
        raise ExternalSchemaError(source)
    return records


def _first_text(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _title_names(root: Any) -> dict[str, str]:
    records = _as_records(root, ("achievementTitles", "titles", "data", "items"), "achievementtitles.json")
    names: dict[str, str] = {}
    for record in records:
        raw_id = record.get(
            "id",
            record.get("titleId", record.get("achievementId", record.get("contentId"))),
        )
        if raw_id is None:
            continue
        name = _first_text(record, "name", "titleName", "localizedName", "displayName")
        if name:
            names[str(raw_id)] = name
    if not names:
        raise ExternalSchemaError("achievementtitles.json")
    return names


def _threshold_records(challenge: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    thresholds = challenge.get("thresholds")
    if isinstance(thresholds, dict):
        return [(str(key).upper(), value) for key, value in thresholds.items() if isinstance(value, dict)]
    if isinstance(thresholds, list):
        records: list[tuple[str, dict[str, Any]]] = []
        for threshold in thresholds:
            if not isinstance(threshold, dict):
                continue
            tier = _first_text(threshold, "tier", "level", "name") or str(threshold.get("id", "NONE"))
            records.append((tier.upper(), threshold))
        return records
    raise ExternalSchemaError("challenges.json")


def _rewards(threshold: dict[str, Any]) -> list[dict[str, Any]]:
    rewards = threshold.get("rewards", threshold.get("reward", []))
    if isinstance(rewards, dict):
        rewards = [rewards]
    return [reward for reward in rewards if isinstance(reward, dict)] if isinstance(rewards, list) else []


def level_to_icon_url(level_to_icon_path: str | None, base_url: str, locale: str) -> str | None:
    if not isinstance(level_to_icon_path, str) or not level_to_icon_path.strip():
        return None
    normalized = level_to_icon_path.strip().replace("\\", "/")
    prefix = "/lol-game-data/"
    if not normalized.startswith(prefix):
        return None
    asset_path = normalized[len(prefix) :].lstrip("/")
    if not asset_path:
        return None
    return f"{base_url.rstrip('/')}/{locale}/{asset_path}"


def parse_catalog(
    challenges_root: Any,
    achievement_titles_root: Any,
    *,
    base_url: str,
    locale: str,
) -> tuple[CatalogTitle, ...]:
    challenge_records = _as_records(challenges_root, ("challenges", "data", "items"), "challenges.json")
    names = _title_names(achievement_titles_root)
    grouped: dict[str, list[CatalogRequirement]] = {}

    for challenge in challenge_records:
        raw_challenge_id = challenge.get("id", challenge.get("challengeId"))
        try:
            challenge_id = int(raw_challenge_id)
        except (TypeError, ValueError) as exc:
            raise ExternalSchemaError("challenges.json") from exc
        challenge_name = _first_text(challenge, "name", "localizedName", "displayName")
        challenge_description = _first_text(challenge, "description", "descriptionShort", "shortDescription")
        if not challenge_name or not challenge_description:
            raise ExternalSchemaError("challenges.json")
        reverse_default = bool(challenge.get("reverseDirection", False))
        previous_value: float | int | None = None
        parsed_thresholds = []
        for tier, threshold in _threshold_records(challenge):
            try:
                target_value = threshold.get("value")
                if target_value is not None:
                    target_value = float(target_value) if isinstance(target_value, float) else int(target_value)
            except (TypeError, ValueError) as exc:
                raise ExternalSchemaError("challenges.json") from exc
            reverse = bool(threshold.get("reverseDirection", reverse_default))
            icon_path = threshold.get("levelToIconPath", threshold.get("iconPath"))
            if icon_path is None:
                icon_path = challenge.get("levelToIconPath", challenge.get("iconPath"))
            if isinstance(icon_path, dict):
                icon_path = icon_path.get(tier) or icon_path.get(tier.upper())
            for reward in _rewards(threshold):
                if reward.get("category") != "TITLE":
                    continue
                raw_title_id = reward.get("id", reward.get("titleId", reward.get("rewardId")))
                if raw_title_id is None:
                    raise ExternalSchemaError("challenges.json")
                title_id = str(raw_title_id)
                title_name = names.get(title_id)
                if not title_name:
                    logger.warning("title_name_missing title_id=%s", title_id)
                    title_name = title_id
                parsed_thresholds.append(
                    (
                        title_id,
                        CatalogRequirement(
                            challenge_id=challenge_id,
                            challenge_name=challenge_name,
                            challenge_description=challenge_description,
                            target_tier=tier,
                            target_value=target_value,
                            reverse_direction=reverse,
                            icon_url=level_to_icon_url(icon_path, base_url, locale),
                            progress_start_value=previous_value if reverse else None,
                        ),
                    )
                )
            if target_value is not None:
                previous_value = target_value

        for title_id, requirement in parsed_thresholds:
            grouped.setdefault(title_id, []).append(requirement)

    if not grouped:
        raise ExternalSchemaError("challenges.json")
    return tuple(
        CatalogTitle(title_id, names.get(title_id, title_id), tuple(requirements))
        for title_id, requirements in grouped.items()
    )


def parse_challenge_graph(
    challenges_root: Any,
    *,
    base_url: str,
    locale: str,
) -> dict[int, CatalogChallenge]:
    """Parse the parent/child challenge hierarchy from CommunityDragon tags."""
    challenge_records = _as_records(challenges_root, ("challenges", "data", "items"), "challenges.json")
    graph: dict[int, CatalogChallenge] = {}
    for challenge in challenge_records:
        raw_challenge_id = challenge.get("id", challenge.get("challengeId"))
        try:
            challenge_id = int(raw_challenge_id)
        except (TypeError, ValueError) as exc:
            raise ExternalSchemaError("challenges.json") from exc
        challenge_name = _first_text(challenge, "name", "localizedName", "displayName")
        challenge_description = _first_text(challenge, "description", "descriptionShort", "shortDescription")
        if not challenge_name or not challenge_description:
            raise ExternalSchemaError("challenges.json")
        thresholds: list[CatalogRequirement] = []
        previous_value: float | int | None = None
        reverse_default = bool(challenge.get("reverseDirection", False))
        for tier, threshold in _threshold_records(challenge):
            try:
                target_value = threshold.get("value")
                if target_value is not None:
                    target_value = float(target_value) if isinstance(target_value, float) else int(target_value)
            except (TypeError, ValueError) as exc:
                raise ExternalSchemaError("challenges.json") from exc
            reverse = bool(threshold.get("reverseDirection", reverse_default))
            icon_path = threshold.get("levelToIconPath", threshold.get("iconPath"))
            if icon_path is None:
                icon_path = challenge.get("levelToIconPath", challenge.get("iconPath"))
            if isinstance(icon_path, dict):
                icon_path = icon_path.get(tier) or icon_path.get(tier.upper())
            thresholds.append(
                CatalogRequirement(
                    challenge_id=challenge_id,
                    challenge_name=challenge_name,
                    challenge_description=challenge_description,
                    target_tier=tier,
                    target_value=target_value,
                    reverse_direction=reverse,
                    icon_url=level_to_icon_url(icon_path, base_url, locale),
                    progress_start_value=previous_value if reverse else None,
                )
            )
            if target_value is not None:
                previous_value = target_value
        if not thresholds:
            continue
        tags = challenge.get("tags") if isinstance(challenge.get("tags"), dict) else {}
        raw_parent = tags.get("parent")
        try:
            parent_id = int(raw_parent) if raw_parent not in (None, "") else None
        except (TypeError, ValueError):
            parent_id = None
        graph[challenge_id] = CatalogChallenge(
            challenge_id=challenge_id,
            challenge_name=challenge_name,
            challenge_description=challenge_description,
            parent_challenge_id=parent_id,
            is_capstone=str(tags.get("isCapstone", "")).upper() == "Y",
            is_category=str(tags.get("isCategory", "")).lower() == "true",
            max_requirement=max(thresholds, key=lambda item: TIER_ORDER.get(item.target_tier, -1)),
        )
    if not graph:
        raise ExternalSchemaError("challenges.json")
    return graph


class TitleCatalogService:
    def __init__(self, client: CommunityDragonClient, ttl_seconds: int):
        self.client = client
        self.cache: LockedMemoryCache[CatalogSnapshot] = LockedMemoryCache(ttl_seconds)

    async def get_snapshot(self) -> CatalogSnapshot:
        entry = self.cache.get("catalog")
        if entry and self.cache.is_fresh(entry):
            logger.info("catalog_cache=fresh")
            return entry.value
        async with self.cache.lock:
            entry = self.cache.get("catalog")
            if entry and self.cache.is_fresh(entry):
                logger.info("catalog_cache=fresh_after_lock")
                return entry.value
            try:
                challenges, titles, locale = await self.client.fetch_catalog_json()
                parsed = parse_catalog(
                    challenges,
                    titles,
                    base_url=self.client.base_url,
                    locale=locale,
                )
                challenge_graph = parse_challenge_graph(
                    challenges,
                    base_url=self.client.base_url,
                    locale=locale,
                )
                snapshot = CatalogSnapshot(tuple(parsed), locale, datetime.now(timezone.utc), challenge_graph)
                self.cache.set("catalog", snapshot)
                logger.info("catalog_cache=updated locale=%s titles=%d", locale, len(snapshot.titles))
                return snapshot
            except Exception as exc:
                if entry:
                    logger.warning("catalog_cache=stale error=%s", type(exc).__name__)
                    return entry.value
                logger.error("catalog_cache=unavailable error=%s", type(exc).__name__)
                raise CatalogUnavailableError() from exc

    async def search(self, query: str = "", limit: int = 50, offset: int = 0) -> tuple[CatalogSnapshot, list[CatalogTitle], int]:
        snapshot = await self.get_snapshot()
        needle = normalize_search(query or "")
        filtered = []
        for title in snapshot.titles:
            haystack = " ".join(
                [title.title_name]
                + [part for requirement in title.requirements for part in (requirement.challenge_name, requirement.challenge_description)]
            )
            if not needle or needle in normalize_search(haystack):
                filtered.append(title)
        return snapshot, filtered[offset : offset + limit], len(filtered)
