from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    riot_api_key: str | None = None
    community_dragon_base_url: str = (
        "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global"
    )
    community_dragon_locale: str = "es_ar"
    static_cache_ttl_seconds: int = 21600
    player_cache_ttl_seconds: int = 60
    http_timeout_seconds: float = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
