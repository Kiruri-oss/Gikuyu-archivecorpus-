import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, CurrentUser, ReviewerUser
from app.models.segment import Segment
from app.models.media import Media
from app.schemas.segment import SegmentCreate, SegmentRead, SegmentUpdate
from app.services.indexing import search_index
from app.core.logging import get_logger

router = APIRouter(prefix="/segments", tags=["segments"])
logger = get_logger(__name__)


@router.get("/media/{media_id}", response_model=list[SegmentRead])
async def list_segments(media_id: uuid.UUID, db: DbSession) -> list[SegmentRead]:
    result = await db.execute(
        select(Segment).where(Segment.media_id == media_id).order_by(Segment.start_seconds)
    )
    return [SegmentRead.model_validate(s) for s in result.scalars().all()]


@router.post("", response_model=SegmentRead, status_code=status.HTTP_201_CREATED)
async def create_segment(payload: SegmentCreate, db: DbSession, user: CurrentUser) -> SegmentRead:
    if payload.end_seconds <= payload.start_seconds:
        raise HTTPException(status_code=422, detail="end_seconds must exceed start_seconds")
    media = await db.get(Media, payload.media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    segment = Segment(
        media_id=payload.media_id,
        start_seconds=payload.start_seconds,
        end_seconds=payload.end_seconds,
        transcript=payload.transcript,
        translation=payload.translation,
        speaker_label=payload.speaker_label,
    )
    db.add(segment)
    await db.flush()

    if segment.transcript:
        try:
            await search_index.index_document("segments", {
                "id": str(segment.id),
                "media_id": str(media.id),
                "transcript": segment.transcript,
                "translation": segment.translation or "",
                "dialect": media.dialect or "",
            })
        except Exception as exc:
            # Keep the transcript record even if the optional search index is offline.
            logger.warning("segment.search_index_failed", segment_id=str(segment.id), error=str(exc))
    return SegmentRead.model_validate(segment)


@router.patch("/{segment_id}", response_model=SegmentRead)
async def update_segment(segment_id: uuid.UUID, payload: SegmentUpdate, db: DbSession, user: CurrentUser) -> SegmentRead:
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    if payload.transcript is not None:
        segment.transcript = payload.transcript
    if payload.translation is not None:
        segment.translation = payload.translation
    await db.flush()
    return SegmentRead.model_validate(segment)


@router.post("/{segment_id}/verify", response_model=SegmentRead)
async def verify_segment(segment_id: uuid.UUID, db: DbSession, _: ReviewerUser) -> SegmentRead:
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    segment.is_verified = True
    await db.flush()
    return SegmentRead.model_validate(segment)