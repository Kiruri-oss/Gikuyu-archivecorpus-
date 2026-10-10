from fastapi import APIRouter, Query
from app.api.v1.auth import router as _auth  # noqa: F401
from app.services.indexing import search_index

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(q: str = Query(min_length=2, max_length=200), limit: int = 20) -> dict:
    media_results = await search_index.search("media", q, min(limit, 50))
    segment_results = await search_index.search("segments", q, min(limit, 50))
    return {
        "query": q,
        "media": media_results.get("hits", []),
        "segments": segment_results.get("hits", []),
    }