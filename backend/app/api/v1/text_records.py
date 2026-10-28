import hashlib
import json
import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.core.deps import DbSession, CurrentUser
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord
from app.schemas.text_record import TextRecordCreate, TextRecordRead, TextRecordSubmissionRead

router = APIRouter(prefix="/text-records", tags=["text records"])


@router.get("", response_model=list[TextRecordRead])
async def list_text_records(
    db: DbSession,
    language_code: str | None = None,
    dialect: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TextRecordRead]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    stmt = (
        select(TextRecord)
        .options(selectinload(TextRecord.source))
        .join(Source, TextRecord.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            TextRecord.language_code == "ki",
            TextRecord.allow_public_display.is_(True),
        )
        .order_by(TextRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    # The public archive is Gĩkũyũ-only; reject explicit requests for other languages.
    if language_code and language_code.strip().lower() != "ki":
        return []
    if language_code:
        stmt = stmt.where(TextRecord.language_code == "ki")
    if dialect:
        stmt = stmt.where(TextRecord.dialect == dialect)
    result = await db.execute(stmt)
    return [TextRecordRead.model_validate(record) for record in result.scalars().all()]


@router.get("/{record_id}", response_model=TextRecordRead)
async def get_text_record(record_id: uuid.UUID, db: DbSession) -> TextRecordRead:
    stmt = (
        select(TextRecord)
        .join(Source, TextRecord.source_id == Source.id)
        .where(
            TextRecord.id == record_id,
            TextRecord.language_code == "ki",
            TextRecord.allow_public_display.is_(True),
            Source.status == SourceStatus.APPROVED,
        )
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Text record not found")
    return TextRecordRead.model_validate(record)


@router.post("", response_model=TextRecordSubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_text_record(
    payload: TextRecordCreate, db: DbSession, user: CurrentUser
) -> TextRecordRead:
    if not payload.consent_to_archive or not payload.confirm_rights:
        raise HTTPException(
            status_code=422,
            detail="Confirm that you have the right to contribute this text and consent to its storage for review.",
        )
    if not payload.language_confirmed or payload.language_code.strip().lower() != "ki":
        raise HTTPException(status_code=422, detail="Only confirmed Gĩkũyũ (language code ki) material may enter this corpus.")

    normalized_body = payload.body.replace("\r\n", "\n").strip()
    digest = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()
    duplicate = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
    if duplicate.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This text already exists in the archive or review queue.")

    source = Source(
        url=f"contribution://text/{uuid.uuid4()}",
        domain="community-contribution",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.PENDING,
        license=payload.license,
        raw_metadata=json.dumps({
            "contributor_id": str(user.id),
            "consent_to_publish": payload.consent_to_publish,
            "allow_research_use": payload.allow_research_use,
            "allow_ai_training": payload.allow_ai_training,
            "allow_commercial_use": payload.allow_commercial_use,
            "consent_to_archive": payload.consent_to_archive,
            "rights_confirmed": payload.confirm_rights,
            "language_confirmed": payload.language_confirmed,
        }),
    )
    db.add(source)
    await db.flush()

    record = TextRecord(
        source_id=source.id,
        source=source,
        contributor_id=user.id,
        title=payload.title,
        body=normalized_body,
        language_code=payload.language_code.lower(),
        author=payload.author,
        year=payload.year,
        dialect=payload.dialect,
        genre=payload.genre,
        sha256=digest,
        size_bytes=len(normalized_body.encode("utf-8")),
        license=payload.license,
        allow_public_display=payload.consent_to_publish,
        allow_research_use=payload.allow_research_use,
        allow_ai_training=payload.allow_ai_training,
        allow_commercial_use=payload.allow_commercial_use,
        notes=payload.notes,
    )
    db.add(record)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This text already exists.") from exc
    return TextRecordSubmissionRead.model_validate(record)
