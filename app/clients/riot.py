import logging

import httpx

from app.clients.http import request_with_retries
from app.errors import AccountNotFoundError, AppError, ConfigurationError, ExternalSchemaError, RiotUnavailableError
from app.routing import account_region_for_platform
from app.utils import riot_id_path

logger = logging.getLogger(__name__)


class RiotClient:
    def __init__(self, client: httpx.AsyncClient, api_key: str | None):
        self.client = client
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ConfigurationError()
        return {"X-Riot-Token": self.api_key}

    async def get_account(self, game_name: str, tag_line: str, platform: str) -> dict:
        region = account_region_for_platform(platform)
        url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{riot_id_path(game_name, tag_line)}"
        response = await request_with_retries(
            self.client,
            "GET",
            url,
            headers=self._headers(),
            platform=platform,
            source="riot-account-v1",
        )
        if response.status_code == 404:
            raise AccountNotFoundError()
        if response.status_code in (401, 403):
            raise RiotUnavailableError()
        if response.status_code >= 500:
            raise RiotUnavailableError()
        if response.status_code >= 400:
            raise AppError("Riot rechazó la consulta de la cuenta.", 502)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalSchemaError("Riot account-v1") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("puuid"), str) or not payload["puuid"]:
            raise ExternalSchemaError("Riot account-v1")
        return payload

    async def get_player_data(self, puuid: str, platform: str) -> dict | list:
        url = f"https://{platform.lower()}.api.riotgames.com/lol/challenges/v1/player-data/{httpx.URL(puuid).raw_path.decode()}"
        response = await request_with_retries(
            self.client,
            "GET",
            url,
            headers=self._headers(),
            platform=platform,
            source="lol-challenges-v1",
        )
        if response.status_code == 404:
            raise AccountNotFoundError()
        if response.status_code in (401, 403):
            raise RiotUnavailableError()
        if response.status_code >= 500:
            raise RiotUnavailableError()
        if response.status_code >= 400:
            raise AppError("Riot rechazó la consulta del progreso.", 502)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalSchemaError("lol-challenges-v1") from exc
        if not isinstance(payload, (dict, list)):
            raise ExternalSchemaError("lol-challenges-v1")
        return payload
