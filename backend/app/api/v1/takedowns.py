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
        previous_notes = source.reviewer_notes or ""
        source.reviewer_notes = f"[takedown hold] {previous_notes}".rstrip()
        await db.flush()

    return TakedownRead.model_validate(takedown)


@router.get("", response_model=list[TakedownRead])
async def list_takedowns(db: DbSession, _: AdminUser) -> list[TakedownRead]:
    result = await db.execute(select(Takedown).order_by(Takedown.created_at.desc()))
    return [TakedownRead.model_validate(t) for t in result.scalars().all()]


async def _delete_index_document(index: str, document_id: uuid.UUID) -> bool:
    try:
        await search_index.delete_document(index, str(document_id))
        return True
    except Exception as exc:
        logger.warning(
            "takedown.index_delete_failed",
            index=index,
            document_id=str(document_id),
            error=str(exc),
        )
        return False


@router.post("/{takedown_id}/action", response_model=TakedownRead)
async def action_takedown(takedown_id: uuid.UUID, db: DbSession, _: AdminUser) -> TakedownRead:
    takedown = await db.get(Takedown, takedown_id)
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown not found")

    cleanup_errors: list[str] = []
    source_result = await db.execute(select(Source).where(Source.url == takedown.url))
    source = source_result.scalar_one_or_none()
    if source:
        # Hide first. Search also checks the database publication state, so a
        # failed index request cannot make a taken-down record visible again.
        source.status = SourceStatus.TAKEN_DOWN
        await db.flush()

        media_result = await db.execute(select(Media).where(Media.source_id == source.id))
        for media in media_result.scalars().all():
            segment_result = await db.execute(select(Segment.id).where(Segment.media_id == media.id))
            segment_ids = [segment_id for (segment_id,) in segment_result.all()]
            segments_cleaned = True
            for segment_id in segment_ids:
                if not await _delete_index_document("segments", segment_id):
                    segments_cleaned = False
                    cleanup_errors.append(f"segment index cleanup failed for {segment_id}")

            media_index_cleaned = await _delete_index_document("media", media.id)
            try:
                storage_service.delete(settings.S3_BUCKET_AUDIO, media.file_key)
                storage_cleaned = True
            except Exception as exc:
                storage_cleaned = False
                cleanup_errors.append(f"object storage cleanup failed for media {media.id}")
                logger.error("takedown.storage_delete_failed", media_id=str(media.id), error=str(exc))

            # Retain the media/segment rows as retry handles if any external
            # cleanup failed. SourceStatus.TAKEN_DOWN keeps them out of public APIs.
            if storage_cleaned and media_index_cleaned and segments_cleaned:
                await db.delete(media)
            elif not media_index_cleaned:
                cleanup_errors.append(f"media index cleanup failed for {media.id}")

        text_result = await db.execute(select(TextRecord).where(TextRecord.source_id == source.id))
        for record in text_result.scalars().all():
            if await _delete_index_document("texts", record.id):
                await db.delete(record)
            else:
                cleanup_errors.append(f"text index cleanup failed for {record.id}")

    if cleanup_errors:
        takedown.status = TakedownStatus.UNDER_REVIEW
        takedown.actioned_at = None
        takedown.admin_notes = (
            "Source hidden. External cleanup remains incomplete and requires retry: "
            + "; ".join(cleanup_errors)[:4000]
        )
    else:
        takedown.status = TakedownStatus.ACTIONED
        takedown.actioned_at = datetime.now(timezone.utc)
        takedown.admin_notes = "Source hidden and available archive records were removed."

    await db.flush()
    return TakedownRead.model_validate(takedown)


@router.post("/{takedown_id}/reject", response_model=TakedownRead)
async def reject_takedown(takedown_id: uuid.UUID, db: DbSession, _: AdminUser) -> TakedownRead:
    """Reject a request after review and restore a source hidden solely for this request."""
    takedown = await db.get(Takedown, takedown_id)
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown not found")
    if takedown.status == TakedownStatus.ACTIONED:
        raise HTTPException(status_code=409, detail="An actioned removal cannot be rejected; restore the source through a separate review.")
    if takedown.status == TakedownStatus.UNDER_REVIEW and (takedown.admin_notes or "").startswith("Source hidden. External cleanup remains incomplete"):
        raise HTTPException(status_code=409, detail="External cleanup is incomplete. Retry the removal action instead of rejecting the request.")

    source_result = await db.execute(select(Source).where(Source.url == takedown.url))
    source = source_result.scalar_one_or_none()
    if (
        source
        and source.status == SourceStatus.PENDING
        and (source.reviewer_notes or "").startswith("[takedown hold]")
    ):
        other_requests = await db.execute(
            select(Takedown.id).where(
                Takedown.url == takedown.url,
                Takedown.id != takedown.id,
                Takedown.status.in_([TakedownStatus.RECEIVED, TakedownStatus.UNDER_REVIEW]),
            )
        )
        if other_requests.first() is None:
            source.status = SourceStatus.APPROVED
            source.reviewer_notes = (source.reviewer_notes or "")[len("[takedown hold]"):].lstrip() or None

    takedown.status = TakedownStatus.REJECTED
    takedown.actioned_at = datetime.now(timezone.utc)
    takedown.admin_notes = "Request rejected after administrator review."
    await db.flush()
    return TakedownRead.model_validate(takedown)
