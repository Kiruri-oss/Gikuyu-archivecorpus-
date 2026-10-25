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
    """Accept a rights complaint for review; never expose the complainant's email publicly."""
    takedown = Takedown(
        url=payload.url.strip(),
        requester_name=payload.requester_name.strip(),
        requester_email=str(payload.requester_email).strip(),
        reason=payload.reason.strip(),
    )
    db.add(takedown)
    await db.flush()
    return TakedownRead.model_validate(takedown)


@router.get("", response_model=list[TakedownRead])
async def list_takedowns(db: DbSession, _: AdminUser) -> list[TakedownRead]:
    result = await db.execute(select(Takedown).order_by(Takedown.created_at.desc()))
    return [TakedownRead.model_validate(item) for item in result.scalars().all()]


@router.post("/{takedown_id}/action", response_model=TakedownRead)
async def action_takedown(
    takedown_id: uuid.UUID, db: DbSession, _: AdminUser
) -> TakedownRead:
    """Remove archived content and its searchable derivatives while preserving the complaint audit trail."""
    takedown = await db.get(Takedown, takedown_id)
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown not found")
    if takedown.status == TakedownStatus.ACTIONED:
        return TakedownRead.model_validate(takedown)

    source_result = await db.execute(select(Source).where(Source.url == takedown.url.strip()))
    source = source_result.scalar_one_or_none()

    if source:
        # Mark it unavailable first. The request-scoped DB transaction commits only
        # after this handler returns successfully.
        source.status = SourceStatus.TAKEN_DOWN
        # Commit the visibility block before external storage/index cleanup. If a
        # storage provider fails, the source stays hidden and the admin can retry.
        await db.commit()

        text_result = await db.execute(select(TextRecord).where(TextRecord.source_id == source.id))
        for record in text_result.scalars().all():
            try:
                await search_index.delete_document("texts", str(record.id))
            except Exception as exc:
                # Search is a derivative, not the archive of record. The search API
                # must also filter hits against approved database records.
                logger.warning("takedown.text_index_delete_failed", record_id=str(record.id), error=str(exc))
            await db.delete(record)

        media_result = await db.execute(select(Media).where(Media.source_id == source.id))
        for media in media_result.scalars().all():
            segment_result = await db.execute(select(Segment).where(Segment.media_id == media.id))
            for segment in segment_result.scalars().all():
                try:
                    await search_index.delete_document("segments", str(segment.id))
                except Exception as exc:
                    logger.warning("takedown.segment_index_delete_failed", segment_id=str(segment.id), error=str(exc))
            try:
                await search_index.delete_document("media", str(media.id))
            except Exception as exc:
                logger.warning("takedown.media_index_delete_failed", media_id=str(media.id), error=str(exc))
            try:
                storage_service.delete(settings.S3_BUCKET_AUDIO, media.file_key)
            except Exception as exc:
                # Do not claim successful removal if the stored media object remains.
                logger.error("takedown.media_storage_delete_failed", media_id=str(media.id), error=str(exc))
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="The source is hidden pending media-storage removal. Retry the takedown action.",
                ) from exc
            await db.delete(media)

    takedown.status = TakedownStatus.ACTIONED
    takedown.actioned_at = datetime.now(timezone.utc)
    await db.flush()
    return TakedownRead.model_validate(takedown)
