import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, ReviewerUser
from app.models.source import Source, SourceStatus
from app.schemas.source import SourceCreate, SourceRead, SourceReview
from app.services.language_detector import language_detector

router = APIRouter(prefix="/sources", tags=["sources"])


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
async def get_source(source_id: uuid.UUID, db: DbSession) -> SourceRead:
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
    source.status = payload.status
    source.reviewed_by = user.id
    source.reviewed_at = datetime.now(timezone.utc)
    source.reviewer_notes = payload.reviewer_notes
    await db.flush()
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
