from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app.core.deps import DbSession
from app.models.media import Media
from app.models.segment import Segment
from app.models.source import Source, SourceStatus
from app.models.text_record import TextRecord

router = APIRouter(prefix="/search", tags=["search"])


def _like_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("")
async def search(
    db: DbSession,
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    """Search approved public corpus records directly in PostgreSQL.

    With no query, return recent approved public records for archive browsing.
    PostgreSQL is the source of truth, so a separate Meilisearch service is optional.
    """
    query = (q or "").strip()
    if query and len(query) < 2:
        raise HTTPException(status_code=400, detail="Enter at least two non-space characters.")
    pattern = _like_pattern(query) if query else None

    media_filters = [Source.status == SourceStatus.APPROVED, Media.allow_public_display.is_(True)]
    if pattern:
        media_filters.append(or_(
            Media.title.ilike(pattern, escape="\\"),
            Media.speaker.ilike(pattern, escape="\\"),
            Media.dialect.ilike(pattern, escape="\\"),
            Media.county.ilike(pattern, escape="\\"),
            Media.genre.ilike(pattern, escape="\\"),
        ))
    media_stmt = (
        select(Media, Source)
        .join(Source, Media.source_id == Source.id)
        .where(*media_filters)
        .order_by(Media.created_at.desc())
        .limit(limit)
    )
    media_result = await db.execute(media_stmt)
    media_hits = []
    for media, source in media_result.all():
        media_hits.append({
            "id": str(media.id),
            "kind": media.kind.value,
            "title": media.title,
            "speaker": media.speaker,
            "dialect": media.dialect,
            "county": media.county,
            "genre": media.genre,
            "duration_seconds": media.duration_seconds,
            "license": media.license,
            "source_url": source.url,
            "lang_score": media.lang_score,
            "created_at": media.created_at.isoformat() if media.created_at else None,
            "allow_research_use": media.allow_research_use,
            "allow_ai_training": media.allow_ai_training,
            "allow_commercial_use": media.allow_commercial_use,
        })

    segment_filters = [Source.status == SourceStatus.APPROVED, Media.allow_public_display.is_(True)]
    if pattern:
        segment_filters.append(or_(
            Segment.transcript.ilike(pattern, escape="\\"),
            Segment.translation.ilike(pattern, escape="\\"),
        ))
    segment_stmt = (
        select(Segment, Media, Source)
        .join(Media, Segment.media_id == Media.id)
        .join(Source, Media.source_id == Source.id)
        .where(*segment_filters)
        .order_by(Segment.start_seconds)
        .limit(limit)
    )
    segment_result = await db.execute(segment_stmt)
    segment_hits = []
    for segment, media, source in segment_result.all():
        segment_hits.append({
            "id": str(segment.id),
            "media_id": str(media.id),
            "media_title": media.title,
            "source_url": source.url,
            "start_seconds": segment.start_seconds,
            "end_seconds": segment.end_seconds,
            "transcript": segment.transcript,
            "translation": segment.translation,
            "speaker_label": segment.speaker_label,
            "is_verified": segment.is_verified,
            "confidence": segment.confidence,
            "dialect": media.dialect,
            "license": media.license,
        })

    text_filters = [Source.status == SourceStatus.APPROVED, TextRecord.allow_public_display.is_(True)]
    if pattern:
        text_filters.append(or_(
            TextRecord.title.ilike(pattern, escape="\\"),
            TextRecord.body.ilike(pattern, escape="\\"),
            TextRecord.author.ilike(pattern, escape="\\"),
            TextRecord.dialect.ilike(pattern, escape="\\"),
            TextRecord.genre.ilike(pattern, escape="\\"),
        ))
    text_stmt = (
        select(TextRecord, Source)
        .join(Source, TextRecord.source_id == Source.id)
        .where(*text_filters)
        .order_by(TextRecord.created_at.desc())
        .limit(limit)
    )
    text_result = await db.execute(text_stmt)
    text_hits = []
    for record, source in text_result.all():
        text_hits.append({
            "id": str(record.id),
            "title": record.title,
            "body": record.body,
            "source_url": source.url,
            "language_code": record.language_code,
            "dialect": record.dialect,
            "genre": record.genre,
            "author": record.author,
            "year": record.year,
            "license": record.license,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "allow_research_use": record.allow_research_use,
            "allow_ai_training": record.allow_ai_training,
            "allow_commercial_use": record.allow_commercial_use,
        })

    return {"query": query, "source": "archive_corpus", "media": media_hits, "segments": segment_hits, "texts": text_hits}
