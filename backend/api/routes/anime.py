from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import AnimeOut
from backend.services import anime_service

router = APIRouter(prefix="/api/anime", tags=["anime"])


@router.get("/search", response_model=AnimeOut)
async def search(q: str = Query(..., description="Anime title to search for")):
    try:
        info = await anime_service.search_anime(q)
    except anime_service.AnimeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return info


@router.get("/random", response_model=AnimeOut)
async def random_anime():
    try:
        info = await anime_service.random_anime()
    except anime_service.AnimeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return info


@router.get("/top", response_model=list[AnimeOut])
async def top_anime(limit: int = 5):
    try:
        return await anime_service.top_anime(limit=limit)
    except anime_service.AnimeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
