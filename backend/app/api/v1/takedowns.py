import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, AdminUser
from app.models.takedown import Takedown, TakedownStatus
from app.models.media import Media
from app.models.source import Source
from app.schemas.takedown import TakedownCreate, TakedownRead
from app.services.storage import storage_service
from app.services.indexing import search_index
from app.core.config import get_settings

router = APIRouter(prefix="/takedowns", tags=["takedowns"])
settings = get_settings()


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
        media_result = await db.execute(select(Media).where(Media.source_id == source.id))
        for media in media_result.scalars().all():
            storage_service.delete(settings.S3_BUCKET_AUDIO, media.file_key)
            await search_index.delete_document("media", str(media.id))
            await db.delete(media)
        source.status = "taken_down"

    takedown.status = TakedownStatus.ACTIONED
    takedown.actioned_at = datetime.now(timezone.utc)
    await db.flush()
    return TakedownRead.model_validate(takedown)