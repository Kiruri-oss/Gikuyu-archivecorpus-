from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import DbSession
from app.models.media import Media
from app.models.segment import Segment
from app.models.source import Source, SourceStatus
from app.models.text_record import TextRecord
from app.services.indexing import search_index

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    db: DbSession,
    q: str = Query(min_length=2, max_length=200),
    limit: int = 20,
) -> dict:
    """Search the index, then enforce current archive permissions against the database."""
    bounded_limit = max(1, min(limit, 50))
    media_results = await search_index.search("media", q, bounded_limit)
    segment_results = await search_index.search("segments", q, bounded_limit)
    text_results = await search_index.search("texts", q, bounded_limit)

    approved_texts = await db.execute(
        select(TextRecord.id)
        .join(Source, TextRecord.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            TextRecord.language_code == "ki",
            TextRecord.allow_public_display.is_(True),
        )
    )
    approved_text_ids = {str(value) for value in approved_texts.scalars().all()}

    approved_media = await db.execute(
        select(Media.id)
        .join(Source, Media.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            Media.allow_public_display.is_(True),
        )
    )
    approved_media_ids = {str(value) for value in approved_media.scalars().all()}

    approved_segments = await db.execute(
        select(Segment.id)
        .join(Media, Segment.media_id == Media.id)
        .join(Source, Media.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            Media.allow_public_display.is_(True),
        )
    )
    approved_segment_ids = {str(value) for value in approved_segments.scalars().all()}

    return {
        "query": q,
        "media": [
            hit for hit in media_results.get("hits", [])
            if str(hit.get("id", "")) in approved_media_ids
        ],
        "segments": [
            hit for hit in segment_results.get("hits", [])
            if str(hit.get("id", "")) in approved_segment_ids
        ],
        "texts": [
            hit for hit in text_results.get("hits", [])
            if str(hit.get("id", "")) in approved_text_ids
        ],
    }
