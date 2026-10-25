import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, ReviewerUser
from app.models.source import Source, SourceStatus
from app.schemas.source import SourceCreate, SourceRead, SourceReview
from app.services.language_detector import language_detector
from app.models.text_record import TextRecord
from app.models.media import Media
from app.models.segment import Segment
from app.services.indexing import search_index
from app.core.logging import get_logger

router = APIRouter(prefix="/sources", tags=["sources"])
logger = get_logger(__name__)


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(payload: SourceCreate, db: DbSession, _: ReviewerUser) -> SourceRead:
    existing = await db.execute(select(Source).where(Source.url == payload.url))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Source already exists")
    source = Source(
        url=payload.url,
        domain=urlparse(payload.url).netloc or "unknown",
        source_type=payload.source_type,
        license=payload.license,
        raw_metadata=payload.raw_metadata,
    )
    db.add(source)
    await db.flush()
    return SourceRead.model_validate(source)


@router.get("", response_model=list[SourceRead])
async def list_sources(
    db: DbSession, _: ReviewerUser, status_filter: SourceStatus | None = None, limit: int = 50
) -> list[SourceRead]:
    stmt = select(Source).order_by(Source.created_at.desc()).limit(max(1, min(limit, 100)))
    if status_filter:
        stmt = stmt.where(Source.status == status_filter)
    result = await db.execute(stmt)
    return [SourceRead.model_validate(source) for source in result.scalars().all()]


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(source_id: uuid.UUID, db: DbSession, _: ReviewerUser) -> SourceRead:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceRead.model_validate(source)


@router.patch("/{source_id}/review", response_model=SourceRead)
async def review_source(
    source_id: uuid.UUID, payload: SourceReview, db: DbSession, user: ReviewerUser
) -> SourceRead:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if payload.status == SourceStatus.PENDING:
        raise HTTPException(status_code=422, detail="A review must approve, reject or take down the source.")
    text_result = await db.execute(select(TextRecord).where(TextRecord.source_id == source.id))
    text_records = text_result.scalars().all()
    media_result = await db.execute(select(Media).where(Media.source_id == source.id))
    media_records = media_result.scalars().all()
    if payload.status == SourceStatus.APPROVED and any(not record.allow_public_display for record in text_records):
        raise HTTPException(status_code=422, detail="The contributor has not consented to public display of this text.")
    if payload.status == SourceStatus.APPROVED and any(not record.allow_public_display for record in media_records):
        raise HTTPException(status_code=422, detail="The contributor has not consented to public display of this media.")
    source.status = payload.status
    source.reviewed_by = user.id
    source.reviewed_at = datetime.now(timezone.utc)
    source.reviewer_notes = payload.reviewer_notes
    await db.flush()
    for record in text_records:
        try:
            if source.status == SourceStatus.APPROVED:
                await search_index.index_document("texts", {
                    "id": str(record.id), "title": record.title, "body": record.body,
                    "language_code": record.language_code, "dialect": record.dialect or "",
                    "genre": record.genre or "", "license": record.license,
                    "source_url": source.url,
                    "allow_ai_training": record.allow_ai_training,
                    "allow_commercial_use": record.allow_commercial_use,
                })
            else:
                await search_index.delete_document("texts", str(record.id))
        except Exception as exc:
            logger.warning("text.search_index_update_failed", text_record_id=str(record.id), error=str(exc))

    for record in media_records:
        try:
            if source.status == SourceStatus.APPROVED:
                await search_index.index_document("media", {
                    "id": str(record.id), "title": record.title,
                    "speaker": record.speaker or "", "dialect": record.dialect or "",
                    "genre": record.genre or "", "license": record.license or "",
                    "allow_ai_training": record.allow_ai_training,
                    "allow_commercial_use": record.allow_commercial_use,
                })
                segment_result = await db.execute(select(Segment).where(Segment.media_id == record.id))
                for segment in segment_result.scalars().all():
                    if segment.transcript or segment.translation:
                        await search_index.index_document("segments", {
                            "id": str(segment.id), "media_id": str(record.id),
                            "transcript": segment.transcript or "",
                            "translation": segment.translation or "",
                            "dialect": record.dialect or "",
                            "language_code": record.dialect or "",
                        })
            else:
                await search_index.delete_document("media", str(record.id))
                segment_result = await db.execute(select(Segment.id).where(Segment.media_id == record.id))
                for segment_id in segment_result.scalars().all():
                    await search_index.delete_document("segments", str(segment_id))
        except Exception as exc:
            logger.warning("media.search_index_update_failed", media_id=str(record.id), error=str(exc))
    return SourceRead.model_validate(source)


@router.post("/{source_id}/classify")
async def classify_source(
    source_id: uuid.UUID, text: str, db: DbSession, _: ReviewerUser
) -> dict:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    lang, score = language_detector.detect(text)
    source.language_confidence = score
    await db.flush()
    return {"language": lang, "confidence": score}
