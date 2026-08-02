import logging

import httpx

from app.clients.http import request_with_retries
from app.errors import ExternalSchemaError

logger = logging.getLogger(__name__)


class CommunityDragonClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str, locale: str):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.locale = locale

    async def _get_json(self, locale: str, filename: str) -> object:
        url = f"{self.base_url}/{locale}/v1/{filename}"
        response = await request_with_retries(self.client, "GET", url, source="communitydragon")
        if response.status_code >= 400:
            raise ExternalSchemaError("CommunityDragon")
        try:
            return response.json()
        except ValueError as exc:
            raise ExternalSchemaError("CommunityDragon") from exc

    async def fetch_catalog_json(self) -> tuple[object, object, str]:
        try:
            challenges, titles = await self._fetch_locale(self.locale)
            return challenges, titles, self.locale
        except Exception as exc:
            logger.warning("communitydragon_locale_failed locale=%s error=%s", self.locale, type(exc).__name__)
            if self.locale == "default":
                raise
            challenges, titles = await self._fetch_locale("default")
            return challenges, titles, "default"

    async def _fetch_locale(self, locale: str) -> tuple[object, object]:
        challenges, titles = await __import__("asyncio").gather(
            self._get_json(locale, "challenges.json"),
            self._get_json(locale, "achievementtitles.json"),
        )
        return challenges, titles
