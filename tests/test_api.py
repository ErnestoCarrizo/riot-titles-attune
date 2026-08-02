import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.clients.community_dragon import CommunityDragonClient
from app.clients.riot import RiotClient
from app.config import Settings
from app.errors import AccountNotFoundError, ExternalTimeoutError, RiotRateLimitError, RiotUnavailableError
from app.main import create_app
from app.services.title_catalog import TitleCatalogService


def test_health_and_platforms():
    with TestClient(create_app(Settings(riot_api_key="key"))) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        platforms = client.get("/api/platforms").json()
        assert any(item["code"] == "LA2" for item in platforms)


@respx.mock
def test_full_progress_uses_riot_id_and_returns_summary(fixture_json):
    account = respx.get("https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Luz%20de%20Luna/TAG").mock(return_value=httpx.Response(200, json={"puuid": "puuid-1"}))
    player = respx.get("https://la2.api.riotgames.com/lol/challenges/v1/player-data/puuid-1").mock(return_value=httpx.Response(200, json=fixture_json("player-data.json")))
    respx.get("https://cdn.test/es_ar/v1/challenges.json").mock(return_value=httpx.Response(200, json=fixture_json("challenges.json")))
    respx.get("https://cdn.test/es_ar/v1/achievementtitles.json").mock(return_value=httpx.Response(200, json=fixture_json("achievementtitles.json")))
    with TestClient(create_app(Settings(riot_api_key="key", community_dragon_base_url="https://cdn.test"))) as client:
        response = client.get("/api/title-progress", params={"riot_id": "Luz de Luna#TAG", "platform": "LA2"})
    assert response.status_code == 200
    assert account.called and player.called
    assert response.json()["player"]["puuid"] == "puuid-1"
    assert response.json()["summary"]["totalTitles"] == 2


@respx.mock
def test_catalog_search_is_accent_insensitive(fixture_json):
    respx.get("https://cdn.test/es_ar/v1/challenges.json").mock(return_value=httpx.Response(200, json=fixture_json("challenges.json")))
    respx.get("https://cdn.test/es_ar/v1/achievementtitles.json").mock(return_value=httpx.Response(200, json=fixture_json("achievementtitles.json")))
    with TestClient(create_app(Settings(riot_api_key="key", community_dragon_base_url="https://cdn.test"))) as client:
        response = client.get("/api/titles", params={"q": "cirujan"})
    assert response.status_code == 200
    assert response.json()["titles"][0]["titleName"] == "Cirujano"


@respx.mock
def test_locale_falls_back_to_default(fixture_json):
    respx.get("https://cdn.test/es_ar/v1/challenges.json").mock(return_value=httpx.Response(404))
    respx.get("https://cdn.test/es_ar/v1/achievementtitles.json").mock(return_value=httpx.Response(404))
    respx.get("https://cdn.test/default/v1/challenges.json").mock(return_value=httpx.Response(200, json=fixture_json("challenges.json")))
    respx.get("https://cdn.test/default/v1/achievementtitles.json").mock(return_value=httpx.Response(200, json=fixture_json("achievementtitles.json")))
    with TestClient(create_app(Settings(riot_api_key="key", community_dragon_base_url="https://cdn.test"))) as client:
        response = client.get("/api/titles")
    assert response.status_code == 200
    assert response.json()["titles"]


@respx.mock
def test_stale_catalog_is_served_when_refresh_fails(fixture_json):
    route_challenges = respx.get("https://cdn.test/es_ar/v1/challenges.json")
    route_titles = respx.get("https://cdn.test/es_ar/v1/achievementtitles.json")
    route_challenges.mock(side_effect=[httpx.Response(200, json=fixture_json("challenges.json")), httpx.Response(500)])
    route_titles.mock(side_effect=[httpx.Response(200, json=fixture_json("achievementtitles.json")), httpx.Response(500)])
    client = httpx.AsyncClient()
    dragon = CommunityDragonClient(client, "https://cdn.test", "es_ar")
    service = TitleCatalogService(dragon, ttl_seconds=0)
    import asyncio
    first = asyncio.run(service.get_snapshot())
    second = asyncio.run(service.get_snapshot())
    assert first.titles == second.titles


@pytest.mark.parametrize(
    ("status", "exception"),
    [(404, AccountNotFoundError), (403, RiotUnavailableError), (429, RiotRateLimitError), (500, RiotUnavailableError)],
)
@respx.mock
def test_riot_errors_are_mapped(status, exception):
    respx.get("https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Name/TAG").mock(return_value=httpx.Response(status))
    async def run():
        async with httpx.AsyncClient() as client:
            riot = RiotClient(client, "key")
            await riot.get_account("Name", "TAG", "LA2")
    with pytest.raises(exception):
        import asyncio
        asyncio.run(run())


def test_missing_api_key_is_clear():
    async def run():
        async with httpx.AsyncClient() as client:
            await RiotClient(client, None).get_account("Name", "TAG", "LA2")
    from app.errors import ConfigurationError
    with pytest.raises(ConfigurationError):
        import asyncio
        asyncio.run(run())


def test_timeout_is_mapped():
    async def handler(request):
        raise httpx.ReadTimeout("slow")
    async def run():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            await RiotClient(client, "key").get_account("Name", "TAG", "LA2")
    with pytest.raises(ExternalTimeoutError):
        import asyncio
        asyncio.run(run())
