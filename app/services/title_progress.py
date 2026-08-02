import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.cache import MemoryCache
from app.clients.riot import RiotClient
from app.errors import ExternalSchemaError
from app.models import (
    MetadataOut,
    PlayerOut,
    RequirementOut,
    SummaryOut,
    ChallengeTreeNodeOut,
    TitleProgressOut,
    TitleProgressResponse,
    TitleTreeResponse,
)
from app.routing import TIER_ORDER, get_platform
from app.services.title_catalog import CatalogChallenge, CatalogRequirement, CatalogSnapshot, CatalogTitle, TitleCatalogService
from app.utils import format_number, parse_riot_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlayerChallenge:
    level: str
    value: float | int | None
    achieved_time: str | None


def parse_player_challenges(payload: dict | list) -> dict[int, PlayerChallenge]:
    records = payload.get("challenges") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ExternalSchemaError("lol-challenges-v1")
    parsed: dict[int, PlayerChallenge] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            challenge_id = int(record.get("challengeId", record.get("id")))
        except (TypeError, ValueError):
            continue
        raw_value = record.get("value")
        try:
            value = float(raw_value) if isinstance(raw_value, float) else (int(raw_value) if raw_value is not None else None)
        except (TypeError, ValueError):
            value = None
        achieved = record.get("achievedTime")
        parsed[challenge_id] = PlayerChallenge(
            level=str(record.get("level", "NONE")).upper(),
            value=value,
            achieved_time=str(achieved) if achieved is not None else None,
        )
    return parsed


def _is_unlocked(requirement: CatalogRequirement, player: PlayerChallenge | None) -> bool:
    if player is None:
        return False
    current_tier = player.level.upper()
    target_tier = requirement.target_tier.upper()
    if current_tier in TIER_ORDER and target_tier in TIER_ORDER:
        return TIER_ORDER[current_tier] >= TIER_ORDER[target_tier]
    if player.value is None or requirement.target_value is None:
        return False
    if requirement.reverse_direction:
        return player.value > 0 and player.value <= requirement.target_value
    return player.value >= requirement.target_value


def _status(requirement: CatalogRequirement, player: PlayerChallenge | None, unlocked: bool) -> str:
    if unlocked:
        return "unlocked"
    if player is None or player.level == "NONE":
        return "not_started"
    if player.value is not None and player.value > 0:
        return "in_progress"
    if player.level in TIER_ORDER:
        return "in_progress"
    return "unknown"


def _progress(requirement: CatalogRequirement, player: PlayerChallenge | None, unlocked: bool) -> tuple[float | None, bool]:
    if unlocked:
        return 100.0, False
    if player is None or player.value is None:
        return (None, True) if requirement.reverse_direction else (0.0 if requirement.target_value and requirement.target_value > 0 else None, False)
    current = float(player.value)
    target = requirement.target_value
    if target is None:
        return None, True
    if not requirement.reverse_direction:
        if target <= 0:
            return None, False
        return round(min(max(current / target * 100, 0), 100), 2), False
    start = requirement.progress_start_value
    if start is None or start <= target:
        return None, True
    percentage = (start - current) / (start - target) * 100
    return round(min(max(percentage, 0), 100), 2), True


def build_requirement(requirement: CatalogRequirement, player: PlayerChallenge | None) -> tuple[RequirementOut, str, bool, float | None, bool]:
    current_tier = player.level if player else "NONE"
    current_value = player.value if player else 0
    unlocked = _is_unlocked(requirement, player)
    status = _status(requirement, player, unlocked)
    progress_percent, progress_is_estimate = _progress(requirement, player, unlocked)
    if requirement.reverse_direction:
        progress_direction = "decrease"
        remaining = None if current_value is None or current_value <= 0 else max(current_value - (requirement.target_value or 0), 0)
        if current_value is None or current_value <= 0:
            remaining_text = "Todavía no hay un valor suficiente para calcular cuánto falta."
        elif unlocked:
            remaining_text = "Objetivo alcanzado."
        else:
            remaining_text = f"Tenés que reducir el valor actual de {format_number(current_value)} a {format_number(requirement.target_value)}."
    else:
        progress_direction = "increase"
        remaining = None if requirement.target_value is None else max((requirement.target_value or 0) - (current_value or 0), 0)
        remaining_text = f"Te faltan {format_number(remaining)} para alcanzar el objetivo."
    output = RequirementOut(
        challengeId=requirement.challenge_id,
        challengeName=requirement.challenge_name,
        challengeDescription=requirement.challenge_description,
        currentTier=current_tier,
        targetTier=requirement.target_tier,
        currentValue=current_value,
        targetValue=requirement.target_value,
        remainingValue=remaining,
        remainingText=remaining_text,
        reverseDirection=requirement.reverse_direction,
        progressDirection=progress_direction,
        iconUrl=requirement.icon_url,
        achievedTime=player.achieved_time if player else None,
    )
    return output, status, unlocked, progress_percent, progress_is_estimate


def build_title(title: CatalogTitle, players: dict[int, PlayerChallenge]) -> TitleProgressOut:
    requirements = []
    statuses = []
    unlocked_values = []
    progress_values = []
    estimates = []
    for requirement in title.requirements:
        output, status, unlocked, progress, estimate = build_requirement(requirement, players.get(requirement.challenge_id))
        requirements.append(output)
        statuses.append(status)
        unlocked_values.append(unlocked)
        if progress is not None:
            progress_values.append(progress)
            estimates.append(estimate)
    unlocked = any(unlocked_values)
    if unlocked:
        status = "unlocked"
        progress = 100.0
        estimate = False
    elif "in_progress" in statuses:
        status = "in_progress"
        progress = max(progress_values) if progress_values else None
        estimate = any(estimates) if estimates else True
    elif "unknown" in statuses:
        status = "unknown"
        progress = max(progress_values) if progress_values else None
        estimate = any(estimates) if estimates else True
    else:
        status = "not_started"
        progress = max(progress_values) if progress_values else (None if any(requirement.reverse_direction for requirement in title.requirements) else 0.0)
        estimate = any(estimates) if estimates else False
    return TitleProgressOut(
        titleId=title.title_id,
        titleName=title.title_name,
        status=status,
        unlocked=unlocked,
        progressPercent=progress,
        progressIsEstimate=estimate,
        requirements=requirements,
    )


def build_summary(titles: list[TitleProgressOut]) -> SummaryOut:
    total = len(titles)
    unlocked = sum(title.status == "unlocked" for title in titles)
    in_progress = sum(title.status == "in_progress" for title in titles)
    not_started = sum(title.status == "not_started" for title in titles)
    unknown = sum(title.status == "unknown" for title in titles)
    closest = sorted(
        (title for title in titles if title.status != "unlocked" and title.status != "unknown" and title.progressPercent is not None),
        key=lambda title: (-title.progressPercent, title.titleName.casefold()),
    )[:5]
    return SummaryOut(
        totalTitles=total,
        unlockedTitles=unlocked,
        lockedTitles=total - unlocked,
        inProgressTitles=in_progress,
        notStartedTitles=not_started,
        unknownTitles=unknown,
        completionPercentage=round(unlocked / total * 100, 2) if total else 0,
        closestTitleIds=[title.titleId for title in closest],
    )


class TitleProgressService:
    def __init__(self, riot: RiotClient, catalog: TitleCatalogService, ttl_seconds: int):
        self.riot = riot
        self.catalog = catalog
        self.player_cache: MemoryCache[tuple[dict[int, PlayerChallenge], datetime]] = MemoryCache(ttl_seconds)

    async def _get_player_challenges(self, puuid: str, platform: str) -> tuple[dict[int, PlayerChallenge], datetime]:
        key = f"{platform.upper()}:{puuid}"
        entry = self.player_cache.get(key)
        if entry and self.player_cache.is_fresh(entry):
            logger.info("player_cache=fresh platform=%s", platform)
            return entry.value
        payload = await self.riot.get_player_data(puuid, platform)
        parsed = parse_player_challenges(payload)
        fetched_at = datetime.now(timezone.utc)
        self.player_cache.set(key, (parsed, fetched_at))
        logger.info("player_cache=updated platform=%s challenges=%d", platform, len(parsed))
        return parsed, fetched_at

    async def get_progress(self, riot_id: str, platform_code: str) -> TitleProgressResponse:
        try:
            platform = get_platform(platform_code)
        except ValueError as exc:
            raise ValueError("La plataforma seleccionada no es válida.") from exc
        game_name, tag_line = parse_riot_id(riot_id)
        account = await self.riot.get_account(game_name, tag_line, platform.code)
        puuid = account["puuid"]
        player_result, catalog_snapshot = await asyncio.gather(
            self._get_player_challenges(puuid, platform.code),
            self.catalog.get_snapshot(),
        )
        player_challenges, player_fetched_at = player_result
        titles = [build_title(title, player_challenges) for title in catalog_snapshot.titles]
        return TitleProgressResponse(
            player=PlayerOut(
                gameName=game_name,
                tagLine=tag_line,
                riotId=f"{game_name}#{tag_line}",
                puuid=puuid,
                platform=platform.code,
            ),
            summary=build_summary(titles),
            titles=titles,
            metadata={
                "locale": catalog_snapshot.locale,
                "catalogSource": "communitydragon",
                "catalogFetchedAt": catalog_snapshot.fetched_at,
                "playerDataFetchedAt": player_fetched_at,
            },
        )

    def _build_tree_node(
        self,
        challenge: CatalogChallenge,
        requirement: CatalogRequirement,
        players: dict[int, PlayerChallenge],
        graph: dict[int, CatalogChallenge],
        children_by_parent: dict[int, list[int]],
        visiting: set[int],
    ) -> ChallengeTreeNodeOut:
        if challenge.challenge_id in visiting:
            return ChallengeTreeNodeOut(
                challengeId=challenge.challenge_id,
                challengeName=challenge.challenge_name,
                challengeDescription=challenge.challenge_description,
                parentChallengeId=challenge.parent_challenge_id,
                isCapstone=challenge.is_capstone,
                isCategory=challenge.is_category,
                status="unknown",
                unlocked=False,
                progressPercent=None,
                progressIsEstimate=True,
                currentTier="NONE",
                targetTier=requirement.target_tier,
                currentValue=None,
                targetValue=requirement.target_value,
                remainingValue=None,
                remainingText="No se pudo resolver la jerarquía completa.",
                reverseDirection=requirement.reverse_direction,
                progressDirection="decrease" if requirement.reverse_direction else "increase",
                iconUrl=requirement.icon_url,
                children=[],
            )
        output, status, unlocked, progress, estimate = build_requirement(
            requirement,
            players.get(challenge.challenge_id),
        )
        next_visiting = visiting | {challenge.challenge_id}
        children = []
        for child_id in sorted(
            children_by_parent.get(challenge.challenge_id, []),
            key=lambda item: (graph[item].challenge_name.casefold(), item),
        ):
            child = graph[child_id]
            children.append(
                self._build_tree_node(
                    child,
                    child.max_requirement,
                    players,
                    graph,
                    children_by_parent,
                    next_visiting,
                )
            )
        return ChallengeTreeNodeOut(
            challengeId=challenge.challenge_id,
            challengeName=challenge.challenge_name,
            challengeDescription=challenge.challenge_description,
            parentChallengeId=challenge.parent_challenge_id,
            isCapstone=challenge.is_capstone,
            isCategory=challenge.is_category,
            status=status,
            unlocked=unlocked,
            progressPercent=progress,
            progressIsEstimate=estimate,
            currentTier=output.currentTier,
            targetTier=output.targetTier,
            currentValue=output.currentValue,
            targetValue=output.targetValue,
            remainingValue=output.remainingValue,
            remainingText=output.remainingText,
            reverseDirection=output.reverseDirection,
            progressDirection=output.progressDirection,
            iconUrl=output.iconUrl,
            children=children,
        )

    async def get_title_tree(self, riot_id: str, platform_code: str, title_id: str) -> TitleTreeResponse:
        try:
            platform = get_platform(platform_code)
        except ValueError as exc:
            raise ValueError("La plataforma seleccionada no es válida.") from exc
        game_name, tag_line = parse_riot_id(riot_id)
        account = await self.riot.get_account(game_name, tag_line, platform.code)
        puuid = account["puuid"]
        player_result, catalog_snapshot = await asyncio.gather(
            self._get_player_challenges(puuid, platform.code),
            self.catalog.get_snapshot(),
        )
        player_challenges, _ = player_result
        title = next((item for item in catalog_snapshot.titles if item.title_id == title_id), None)
        if title is None:
            from app.errors import TitleNotFoundError

            raise TitleNotFoundError()
        title_progress = build_title(title, player_challenges)
        graph = catalog_snapshot.challenge_graph
        children_by_parent: dict[int, list[int]] = {}
        for challenge in graph.values():
            if challenge.parent_challenge_id is not None:
                children_by_parent.setdefault(challenge.parent_challenge_id, []).append(challenge.challenge_id)
        roots = []
        for requirement in title.requirements:
            challenge = graph.get(requirement.challenge_id)
            if challenge is None:
                continue
            roots.append(
                self._build_tree_node(
                    challenge,
                    requirement,
                    player_challenges,
                    graph,
                    children_by_parent,
                    set(),
                )
            )
        if not roots:
            from app.errors import ExternalSchemaError

            raise ExternalSchemaError("challenges.json")
        return TitleTreeResponse(
            titleId=title.title_id,
            titleName=title.title_name,
            status=title_progress.status,
            progressPercent=title_progress.progressPercent,
            roots=roots,
        )
