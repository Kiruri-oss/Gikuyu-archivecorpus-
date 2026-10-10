import uuid
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, ReviewerUser
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceRead
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


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(source_id: uuid.UUID, db: DbSession) -> SourceRead:
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
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