import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.clients.community_dragon import CommunityDragonClient
from app.clients.riot import RiotClient
from app.config import Settings, get_settings
from app.errors import AppError
from app.routers.api import router as api_router
from app.services.title_catalog import TitleCatalogService
from app.services.title_progress import TitleProgressService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = httpx.AsyncClient(timeout=app_settings.http_timeout_seconds)
        riot = RiotClient(client, app_settings.riot_api_key)
        community_dragon = CommunityDragonClient(
            client,
            app_settings.community_dragon_base_url,
            app_settings.community_dragon_locale,
        )
        catalog_service = TitleCatalogService(community_dragon, app_settings.static_cache_ttl_seconds)
        app.state.http_client = client
        app.state.riot_client = riot
        app.state.catalog_service = catalog_service
        app.state.progress_service = TitleProgressService(riot, catalog_service, app_settings.player_cache_ttl_seconds)
        yield
        await client.aclose()

    app = FastAPI(title="Riot Titles Attune", lifespan=lifespan)

    @app.exception_handler(AppError)
    async def app_error_handler(_, exc: AppError) -> JSONResponse:
        headers = {"Retry-After": exc.retry_after} if exc.retry_after else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)

    app.include_router(api_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
