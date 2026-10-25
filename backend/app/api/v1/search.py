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


def _valid_hit_ids(hits: list[dict]) -> list[uuid.UUID]:
    identifiers: list[uuid.UUID] = []
    for hit in hits:
        try:
            identifiers.append(uuid.UUID(str(hit.get("id", ""))))
        except (ValueError, TypeError, AttributeError):
            continue
    return list(dict.fromkeys(identifiers))


def _visible_hits(hits: list[dict], visible_ids: set[str]) -> list[dict]:
    visible: list[dict] = []
    for hit in hits:
        try:
            identifier = str(uuid.UUID(str(hit.get("id", ""))))
        except (ValueError, TypeError, AttributeError):
            continue
        if identifier in visible_ids:
            visible.append(hit)
    return visible


@router.get("")
async def search(
    db: DbSession,
    q: str = Query(min_length=2, max_length=200),
    limit: int = 20,
) -> dict:
    bounded_limit = max(1, min(limit, 50))
    media_hits = (await search_index.search("media", q, bounded_limit)).get("hits", [])
    segment_hits = (await search_index.search("segments", q, bounded_limit)).get("hits", [])
    text_hits = (await search_index.search("texts", q, bounded_limit)).get("hits", [])

    # Meilisearch is an index, not the authority for publication state. Validate
    # every hit against the database so pending, rejected or taken-down sources
    # cannot leak through stale index documents after a removal request.
    media_ids = _valid_hit_ids(media_hits)
    segment_ids = _valid_hit_ids(segment_hits)
    text_ids = _valid_hit_ids(text_hits)

    visible_media: set[str] = set()
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
        visible_media = {str(identifier) for identifier in result.scalars().all()}

    visible_segments: set[str] = set()
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
        visible_segments = {str(identifier) for identifier in result.scalars().all()}

    visible_texts: set[str] = set()
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
        visible_texts = {str(identifier) for identifier in result.scalars().all()}

    return {
        "query": q,
        "media": _visible_hits(media_hits, visible_media),
        "segments": _visible_hits(segment_hits, visible_segments),
        "texts": _visible_hits(text_hits, visible_texts),
    }
