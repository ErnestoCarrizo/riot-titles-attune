from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Status = Literal["unlocked", "in_progress", "not_started", "unknown"]


class PlatformOut(BaseModel):
    code: str
    name: str


class RequirementOut(BaseModel):
    challengeId: int
    challengeName: str
    challengeDescription: str
    currentTier: str
    targetTier: str
    currentValue: float | int | None
    targetValue: float | int | None
    remainingValue: float | int | None
    remainingText: str
    reverseDirection: bool
    progressDirection: Literal["increase", "decrease"]
    iconUrl: str | None
    achievedTime: str | None


class TitleProgressOut(BaseModel):
    titleId: str
    titleName: str
    status: Status
    unlocked: bool
    progressPercent: float | None
    progressIsEstimate: bool
    requirements: list[RequirementOut]


class PlayerOut(BaseModel):
    gameName: str
    tagLine: str
    riotId: str
    puuid: str
    platform: str


class SummaryOut(BaseModel):
    totalTitles: int
    unlockedTitles: int
    lockedTitles: int
    inProgressTitles: int
    notStartedTitles: int
    unknownTitles: int
    completionPercentage: float
    closestTitleIds: list[str]


class MetadataOut(BaseModel):
    locale: str
    catalogSource: str
    catalogFetchedAt: datetime
    playerDataFetchedAt: datetime


class TitleProgressResponse(BaseModel):
    player: PlayerOut
    summary: SummaryOut
    titles: list[TitleProgressOut]
    metadata: MetadataOut


class ChallengeTreeNodeOut(BaseModel):
    challengeId: int
    challengeName: str
    challengeDescription: str
    parentChallengeId: int | None
    isCapstone: bool
    isCategory: bool
    status: Status
    unlocked: bool
    progressPercent: float | None
    progressIsEstimate: bool
    currentTier: str
    targetTier: str
    currentValue: float | int | None
    targetValue: float | int | None
    remainingValue: float | int | None
    remainingText: str
    reverseDirection: bool
    progressDirection: Literal["increase", "decrease"]
    iconUrl: str | None
    children: list["ChallengeTreeNodeOut"] = Field(default_factory=list)


class TitleTreeResponse(BaseModel):
    titleId: str
    titleName: str
    status: Status
    progressPercent: float | None
    roots: list[ChallengeTreeNodeOut]


ChallengeTreeNodeOut.model_rebuild()


class CatalogRequirementOut(BaseModel):
    challengeId: int
    challengeName: str
    challengeDescription: str
    targetTier: str
    targetValue: float | int | None
    reverseDirection: bool
    iconUrl: str | None


class CatalogTitleOut(BaseModel):
    titleId: str
    titleName: str
    requirements: list[CatalogRequirementOut]


class CatalogResponse(BaseModel):
    total: int
    limit: int
    offset: int
    titles: list[CatalogTitleOut]


class HealthOut(BaseModel):
    status: Literal["ok"]
