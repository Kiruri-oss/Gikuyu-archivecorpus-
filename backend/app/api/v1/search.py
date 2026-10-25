from fastapi import APIRouter, Query
from app.services.indexing import search_index

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(q: str = Query(min_length=2, max_length=200), limit: int = 20) -> dict:
    bounded_limit = max(1, min(limit, 50))
    media_results = await search_index.search("media", q, bounded_limit)
    segment_results = await search_index.search("segments", q, bounded_limit)
    text_results = await search_index.search("texts", q, bounded_limit)
    return {
        "query": q,
        "media": media_results.get("hits", []),
        "segments": segment_results.get("hits", []),
        "texts": text_results.get("hits", []),
    }
