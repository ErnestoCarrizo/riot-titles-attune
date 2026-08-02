from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.models import CatalogResponse, HealthOut, PlatformOut, TitleProgressResponse, TitleTreeResponse
from app.routing import PLATFORMS, get_platform
from app.services.title_catalog import TitleCatalogService
from app.services.title_progress import TitleProgressService
from app.utils import parse_riot_id

router = APIRouter(prefix="/api")


def _service(request: Request, name: str):
    return getattr(request.app.state, name)


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok")


@router.get("/platforms", response_model=list[PlatformOut])
async def platforms() -> list[PlatformOut]:
    return [PlatformOut(code=platform.code, name=platform.name) for platform in PLATFORMS]


@router.get("/titles", response_model=CatalogResponse)
async def titles(
    request: Request,
    q: str = Query(default=""),
    status: str = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CatalogResponse:
    if status != "all":
        raise HTTPException(status_code=400, detail="/api/titles es un catálogo puro; filtrá el estado en una consulta de progreso.")
    catalog: TitleCatalogService = _service(request, "catalog_service")
    snapshot, selected, total = await catalog.search(q, limit, offset)
    return CatalogResponse(
        total=total,
        limit=limit,
        offset=offset,
        titles=[
            {
                "titleId": title.title_id,
                "titleName": title.title_name,
                "requirements": [
                    {
                        "challengeId": requirement.challenge_id,
                        "challengeName": requirement.challenge_name,
                        "challengeDescription": requirement.challenge_description,
                        "targetTier": requirement.target_tier,
                        "targetValue": requirement.target_value,
                        "reverseDirection": requirement.reverse_direction,
                        "iconUrl": requirement.icon_url,
                    }
                    for requirement in title.requirements
                ],
            }
            for title in selected
        ],
    )


@router.get("/title-progress", response_model=TitleProgressResponse)
async def title_progress(
    request: Request,
    riot_id: str = Query(...),
    platform: str = Query(...),
) -> TitleProgressResponse:
    try:
        parse_riot_id(riot_id)
        get_platform(platform)
        service: TitleProgressService = _service(request, "progress_service")
        return await service.get_progress(riot_id, platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AppError as exc:
        headers = {"Retry-After": exc.retry_after} if exc.retry_after else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)


@router.get("/title-tree", response_model=TitleTreeResponse)
async def title_tree(
    request: Request,
    riot_id: str = Query(...),
    platform: str = Query(...),
    title_id: str = Query(...),
) -> TitleTreeResponse:
    try:
        parse_riot_id(riot_id)
        get_platform(platform)
        service: TitleProgressService = _service(request, "progress_service")
        return await service.get_title_tree(riot_id, platform, title_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AppError as exc:
        headers = {"Retry-After": exc.retry_after} if exc.retry_after else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)
