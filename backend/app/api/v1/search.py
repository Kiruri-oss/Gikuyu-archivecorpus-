import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import DbSession
from app.models.media import Media
from app.models.segment import Segment
from app.models.source import Source, SourceStatus
from app.models.text_record import TextRecord
from app.services.indexing import search_index

router = APIRouter(prefix="/search", tags=["search"])


def _uuid_ids(hits: list[dict]) -> list[uuid.UUID]:
    values: list[uuid.UUID] = []
    for hit in hits:
        try:
            values.append(uuid.UUID(str(hit.get("id", ""))))
        except (ValueError, TypeError, AttributeError):
            continue
    return list(dict.fromkeys(values))


@router.get("")
async def search(
    db: DbSession,
    q: str = Query(min_length=2, max_length=200),
    limit: int = 20,
) -> dict:
    """Search the index, then enforce live archive status and Gĩkũyũ scope in the database."""
    bounded_limit = max(1, min(limit, 50))
    media_hits = (await search_index.search("media", q, bounded_limit)).get("hits", [])
    segment_hits = (await search_index.search("segments", q, bounded_limit)).get("hits", [])
    text_hits = (await search_index.search("texts", q, bounded_limit)).get("hits", [])

    media_ids = _uuid_ids(media_hits)
    segment_ids = _uuid_ids(segment_hits)
    text_ids = _uuid_ids(text_hits)

    approved_media_ids: set[str] = set()
    if media_ids:
        result = await db.execute(
            select(Media.id)
            .join(Source, Media.source_id == Source.id)
            .where(
                Media.id.in_(media_ids),
                Source.status == SourceStatus.APPROVED,
                Media.allow_public_display.is_(True),
            )
        )
        approved_media_ids = {str(value) for value in result.scalars().all()}

    approved_segment_ids: set[str] = set()
    if segment_ids:
        result = await db.execute(
            select(Segment.id)
            .join(Media, Segment.media_id == Media.id)
            .join(Source, Media.source_id == Source.id)
            .where(
                Segment.id.in_(segment_ids),
                Source.status == SourceStatus.APPROVED,
                Media.allow_public_display.is_(True),
            )
        )
        approved_segment_ids = {str(value) for value in result.scalars().all()}

    approved_text_ids: set[str] = set()
    if text_ids:
        result = await db.execute(
            select(TextRecord.id)
            .join(Source, TextRecord.source_id == Source.id)
            .where(
                TextRecord.id.in_(text_ids),
                Source.status == SourceStatus.APPROVED,
                TextRecord.language_code == "ki",
                TextRecord.allow_public_display.is_(True),
            )
        )
        approved_text_ids = {str(value) for value in result.scalars().all()}

    visible_media = [
        {**hit, "kind": hit.get("kind", "audio"), "source_name": "Gĩkũyũ Archive Corpus"}
        for hit in media_hits
        if str(hit.get("id", "")) in approved_media_ids
    ]
    visible_texts = [
        {
            **hit,
            "kind": "text",
            "summary": hit.get("body", ""),
            "source_name": "Gĩkũyũ Archive Corpus",
        }
        for hit in text_hits
        if str(hit.get("id", "")) in approved_text_ids
    ]

    visible_ids = {str(hit.get("id", "")) for hit in visible_media + visible_texts}
    visible_segments = [
        hit for hit in segment_hits
        if str(hit.get("id", "")) in approved_segment_ids
    ]
    transcript_matches = []
    for hit in visible_segments:
        media_id = str(hit.get("media_id", ""))
        if not media_id or media_id not in approved_media_ids or media_id in visible_ids:
            continue
        visible_ids.add(media_id)
        summary = " ".join(part for part in (hit.get("transcript"), hit.get("translation")) if part)
        transcript_matches.append({
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
            "summary": summary,
            "source_name": "Gĩkũyũ Archive Corpus",
        })

    return {
        "query": q,
        "media": visible_media + visible_texts + transcript_matches,
        "segments": visible_segments,
        "texts": visible_texts,
    }
