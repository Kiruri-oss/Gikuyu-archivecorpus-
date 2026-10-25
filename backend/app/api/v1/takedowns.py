import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DbSession, AdminUser
from app.core.logging import get_logger
from app.models.media import Media
from app.models.segment import Segment
from app.models.source import Source, SourceStatus
from app.models.takedown import Takedown, TakedownStatus
from app.models.text_record import TextRecord
from app.schemas.takedown import TakedownCreate, TakedownRead
from app.services.indexing import search_index
from app.services.storage import storage_service

router = APIRouter(prefix="/takedowns", tags=["takedowns"])
settings = get_settings()
logger = get_logger(__name__)


@router.post("", response_model=TakedownRead, status_code=status.HTTP_201_CREATED)
async def submit_takedown(payload: TakedownCreate, db: DbSession) -> TakedownRead:
    takedown = Takedown(
        url=payload.url,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        reason=payload.reason,
    )
    db.add(takedown)
    await db.flush()

    # Hide an approved source immediately when a removal request is received.
    # Keep the record and provenance while the request is queued for review.
    source_result = await db.execute(select(Source).where(Source.url == payload.url))
    source = source_result.scalar_one_or_none()
    if source and source.status == SourceStatus.APPROVED:
        source.status = SourceStatus.PENDING
        source.reviewer_notes = f"Temporarily hidden while takedown request {takedown.id} is reviewed."
        await db.flush()

    return TakedownRead.model_validate(takedown)


@router.get("", response_model=list[TakedownRead])
async def list_takedowns(db: DbSession, _: AdminUser) -> list[TakedownRead]:
    result = await db.execute(select(Takedown).order_by(Takedown.created_at.desc()))
    return [TakedownRead.model_validate(t) for t in result.scalars().all()]


@router.post("/{takedown_id}/action", response_model=TakedownRead)
async def action_takedown(takedown_id: uuid.UUID, db: DbSession, _: AdminUser) -> TakedownRead:
    takedown = await db.get(Takedown, takedown_id)
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown not found")

    source_result = await db.execute(select(Source).where(Source.url == takedown.url))
    source = source_result.scalar_one_or_none()
    if source:
        # Hide the source first so stale index entries cannot keep it publicly visible.
        source.status = SourceStatus.TAKEN_DOWN
        await db.flush()

        media_result = await db.execute(select(Media).where(Media.source_id == source.id))
        for media in media_result.scalars().all():
            segment_result = await db.execute(select(Segment.id).where(Segment.media_id == media.id))
            for (segment_id,) in segment_result.all():
                try:
                    await search_index.delete_document("segments", str(segment_id))
                except Exception as exc:
                    logger.warning("takedown.segment_index_delete_failed", segment_id=str(segment_id), error=str(exc))
            try:
                storage_service.delete(settings.S3_BUCKET_AUDIO, media.file_key)
            except Exception as exc:
                logger.error("takedown.storage_delete_failed", media_id=str(media.id), error=str(exc))
            try:
                await search_index.delete_document("media", str(media.id))
            except Exception as exc:
                logger.warning("takedown.media_index_delete_failed", media_id=str(media.id), error=str(exc))
            await db.delete(media)

        text_result = await db.execute(select(TextRecord).where(TextRecord.source_id == source.id))
        for record in text_result.scalars().all():
            try:
                await search_index.delete_document("texts", str(record.id))
            except Exception as exc:
                logger.warning("takedown.text_index_delete_failed", record_id=str(record.id), error=str(exc))
            await db.delete(record)

    takedown.status = TakedownStatus.ACTIONED
    takedown.actioned_at = datetime.now(timezone.utc)
    await db.flush()
    return TakedownRead.model_validate(takedown)
