import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select

from app.core.deps import DbSession, CurrentUser, ReviewerUser
from app.models.media import Media, MediaKind
from app.models.source import Source, SourceType, SourceStatus
from app.schemas.media import MediaRead, MediaDetail, MediaCreate
from app.services.storage import storage_service
from app.services.language_detector import language_detector
from app.services.dedup import dedup_service
from app.services.indexing import search_index
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/media", tags=["media"])
settings = get_settings()
logger = get_logger(__name__)

def _build_media_detail(media: Media) -> MediaDetail:
    data = MediaRead.model_validate(media).model_dump()
    data.update({
        "file_url": storage_service.presigned_url(settings.S3_BUCKET_AUDIO, media.file_key),
        "sha256": media.sha256,
        "size_bytes": media.size_bytes,
    })
    return MediaDetail.model_validate(data)


@router.get("", response_model=list[MediaRead])
async def list_media(
    db: DbSession,
    dialect: str | None = None,
    genre: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MediaRead]:
    stmt = select(Media).order_by(Media.created_at.desc()).limit(min(limit, 100)).offset(offset)
    if dialect:
        stmt = stmt.where(Media.dialect == dialect)
    if genre:
        stmt = stmt.where(Media.genre == genre)
    result = await db.execute(stmt)
    return [MediaRead.model_validate(m) for m in result.scalars().all()]


@router.get("/{media_id}", response_model=MediaDetail)
async def get_media(media_id: uuid.UUID, db: DbSession) -> MediaDetail:
    media = await db.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return _build_media_detail(media)


@router.post("", response_model=MediaDetail, status_code=status.HTTP_201_CREATED)
async def upload_media(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    meta: str = Form(...),
) -> MediaDetail:
    import json
    parsed = MediaCreate.model_validate(json.loads(meta))

    raw = await file.read()
    if len(raw) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")

    sha = storage_service.compute_sha256(raw)
    if await dedup_service.media_exists(db, sha):
        raise HTTPException(status_code=409, detail="Duplicate media (sha256 match)")

    file_key = f"{user.id}/{sha[:2]}/{sha}"
    storage_service.upload(settings.S3_BUCKET_AUDIO, file_key, raw, file.content_type or "application/octet-stream")

    source = Source(
        url=f"upload://{sha}",
        domain="user_upload",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.APPROVED,
    )
    db.add(source)
    await db.flush()

    lang, score = language_detector.detect(parsed.title)
    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        title=parsed.title,
        speaker=parsed.speaker,
        dialect=parsed.dialect,
        county=parsed.county,
        genre=parsed.genre,
        file_key=file_key,
        sha256=sha,
        size_bytes=len(raw),
        mime_type=file.content_type,
        lang_score=score,
        license=parsed.license,
        notes=parsed.notes,
    )
    db.add(media)
    await db.flush()

    try:
        await search_index.index_document("media", {
            "id": str(media.id),
            "title": media.title,
            "speaker": media.speaker or "",
            "dialect": media.dialect or "",
            "genre": media.genre or "",
        })
    except Exception as exc:
        # Search is a secondary index; do not turn a successful archive write into a failed upload.
        logger.warning("media.search_index_failed", media_id=str(media.id), error=str(exc))

    detail = MediaDetail.model_validate(media)
    detail.file_url = storage_service.presigned_url(settings.S3_BUCKET_AUDIO, media.file_key)
    return detail


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: uuid.UUID, db: DbSession, _: ReviewerUser) -> None:
    media = await db.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    storage_service.delete(settings.S3_BUCKET_AUDIO, media.file_key)
    try:
        await search_index.delete_document("media", str(media.id))
    except Exception as exc:
        logger.warning("media.search_index_delete_failed", media_id=str(media.id), error=str(exc))
    await db.delete(media)