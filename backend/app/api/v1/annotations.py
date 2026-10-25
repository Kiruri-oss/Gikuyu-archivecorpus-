import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, CurrentUser
from app.models.annotation import Annotation
from app.models.segment import Segment
from app.models.media import Media
from app.models.source import Source, SourceStatus
from app.schemas.annotation import AnnotationCreate, AnnotationRead

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("/segment/{segment_id}", response_model=list[AnnotationRead])
async def list_annotations(segment_id: uuid.UUID, db: DbSession) -> list[AnnotationRead]:
    visible = await db.execute(
        select(Segment.id)
        .join(Media, Segment.media_id == Media.id)
        .join(Source, Media.source_id == Source.id)
        .where(Segment.id == segment_id, Source.status == SourceStatus.APPROVED, Media.allow_public_display.is_(True))
    )
    if visible.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    result = await db.execute(
        select(Annotation).where(Annotation.segment_id == segment_id)
    )
    return [AnnotationRead.model_validate(a) for a in result.scalars().all()]


@router.post(
    "/segment/{segment_id}",
    response_model=AnnotationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_annotation(
    segment_id: uuid.UUID, payload: AnnotationCreate, db: DbSession, user: CurrentUser
) -> AnnotationRead:
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    annotation = Annotation(
        segment_id=segment_id,
        user_id=user.id,
        annotation_type=payload.annotation_type,
        value=payload.value,
        confidence=payload.confidence,
        notes=payload.notes,
    )
    db.add(annotation)
    await db.flush()
    return AnnotationRead.model_validate(annotation)