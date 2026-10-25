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
    """Search the index, then enforce live archive status and Gĩkũyũ scope in the database."""
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

    media_hits = [
        {
            **hit,
            "kind": hit.get("kind", "audio"),
            "source_name": "Gĩkũyũ Archive Corpus",
        }
        for hit in media_results.get("hits", [])
        if str(hit.get("id", "")) in approved_media_ids
    ]
    text_hits = [
        {
            **hit,
            "kind": "text",
            "summary": hit.get("body", ""),
            "source_name": "Gĩkũyũ Archive Corpus",
        }
        for hit in text_results.get("hits", [])
        if str(hit.get("id", "")) in approved_text_ids
    ]

    # Transcript matches lead to the owning recording's detail page. Avoid
    # duplicating a recording already present in the media search results.
    visible_ids = {str(hit.get("id", "")) for hit in media_hits + text_hits}
    segment_hits = [
        hit for hit in segment_results.get("hits", [])
        if str(hit.get("id", "")) in approved_segment_ids
    ]
    transcript_hits = []
    for hit in segment_hits:
        media_id = str(hit.get("media_id", ""))
        if not media_id or media_id not in approved_media_ids or media_id in visible_ids:
            continue
        visible_ids.add(media_id)
        transcript = " ".join(part for part in (hit.get("transcript"), hit.get("translation")) if part)
        transcript_hits.append({
            "id": media_id,
            "kind": "audio",
            "title": "Recording with matching transcript",
            "speaker": None,
            "dialect": hit.get("dialect") or "Gĩkũyũ",
            "county": None,
            "genre": "Transcript match",
            "duration_seconds": None,
            "license": None,
            "lang_score": None,
            "summary": transcript,
            "source_name": "Gĩkũyũ Archive Corpus",
        })

    return {
        "query": q,
        "media": media_hits + text_hits + transcript_hits,
        "segments": segment_hits,
        "texts": text_hits,
    }
