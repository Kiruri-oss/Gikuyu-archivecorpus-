import asyncio
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession, CurrentUser, ReviewerUser
from app.models.media import Media, MediaKind
from app.models.source import Source, SourceType, SourceStatus
from app.schemas.media import MediaRead, MediaDetail, MediaCreate, MediaSubmissionDetail
from app.services.storage import storage_service
from app.services.dedup import dedup_service
from app.services.indexing import search_index
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/media", tags=["media"])
settings = get_settings()
logger = get_logger(__name__)

def _build_media_read(media: Media) -> MediaRead:
    data = MediaRead.model_validate(media).model_dump()
    source = media.__dict__.get("source")
    source_url = source.url if source else None
    data["source_url"] = source_url if source_url and source_url.startswith(("http://", "https://")) else None
    return MediaRead.model_validate(data)


def _build_media_detail(media: Media) -> MediaDetail:
    data = _build_media_read(media).model_dump()
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
    stmt = select(Media).options(selectinload(Media.source)).join(Source, Media.source_id == Source.id).where(Source.status == SourceStatus.APPROVED, Media.language_code == "ki", Media.allow_public_display.is_(True)).order_by(Media.created_at.desc()).limit(max(1, min(limit, 100))).offset(max(0, offset))
    if dialect:
        stmt = stmt.where(Media.dialect == dialect)
    if genre:
        stmt = stmt.where(Media.genre == genre)
    result = await db.execute(stmt)
    return [_build_media_read(m) for m in result.scalars().all()]


@router.get("/{media_id}", response_model=MediaDetail)
async def get_media(media_id: uuid.UUID, db: DbSession) -> MediaDetail:
    stmt = select(Media).options(selectinload(Media.source)).join(Source, Media.source_id == Source.id).where(Media.id == media_id, Source.status == SourceStatus.APPROVED, Media.allow_public_display.is_(True))
    result = await db.execute(stmt)
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return _build_media_detail(media)


@router.post("", response_model=MediaSubmissionDetail, status_code=status.HTTP_201_CREATED)
async def upload_media(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    meta: str = Form(...),
 ) -> MediaSubmissionDetail:
    import json
    parsed = MediaCreate.model_validate(json.loads(meta))
    if not parsed.consent_to_archive or not parsed.confirm_rights:
        raise HTTPException(status_code=422, detail="Confirm your right to contribute this recording and consent to its storage for review.")
    if not parsed.speaker_consent_confirmed:
        raise HTTPException(status_code=422, detail="Confirm that the speaker(s) consented to this recording and its submission.")
    if not parsed.language_confirmed:
        raise HTTPException(status_code=422, detail="Confirm that this recording contains Gĩkũyũ language material.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    allowed_extensions = (".wav", ".mp3", ".m4a", ".mp4", ".ogg", ".opus", ".webm", ".flac", ".aac")
    if not content_type.startswith("audio/") and not filename.endswith(allowed_extensions):
        raise HTTPException(status_code=415, detail="Upload an audio file such as WAV, MP3, M4A, OGG or WebM.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size is not None and file.size > max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")
    try:
        sha, size_bytes = await asyncio.to_thread(
            storage_service.compute_sha256_file, file.file, max_bytes
        )
    except ValueError:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size") from None

    if await dedup_service.media_exists(db, sha):
        raise HTTPException(status_code=409, detail="Duplicate media (sha256 match)")

    file_key = f"{user.id}/{sha[:2]}/{sha}"
    await asyncio.to_thread(
        storage_service.upload_fileobj,
        settings.S3_BUCKET_AUDIO,
        file_key,
        file.file,
        content_type or "application/octet-stream",
    )

    source = Source(
        url=f"upload://{sha}",
        domain="user_upload",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.PENDING,
        license=parsed.license,
        raw_metadata=json.dumps({
            "contributor_id": str(user.id),
            "consent_to_publish": parsed.consent_to_publish,
            "allow_research_use": parsed.allow_research_use,
            "allow_ai_training": parsed.allow_ai_training,
            "allow_commercial_use": parsed.allow_commercial_use,
            "consent_to_archive": parsed.consent_to_archive,
            "rights_confirmed": parsed.confirm_rights,
            "speaker_consent_confirmed": parsed.speaker_consent_confirmed,
            "language_confirmed": parsed.language_confirmed,
            "speaker_consent_recorded_at": datetime.now(timezone.utc).isoformat(),
        }),
    )
    db.add(source)
    await db.flush()

    score = None  # The contributor attests to language; title text is not speech detection.
    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        language_code=parsed.language_code,
        title=parsed.title,
        speaker=parsed.speaker,
        dialect=parsed.dialect,
        county=parsed.county,
        genre=parsed.genre,
        file_key=file_key,
        sha256=sha,
        size_bytes=size_bytes,
        mime_type=content_type or "application/octet-stream",
        lang_score=score,
        license=parsed.license,
        allow_public_display=parsed.consent_to_publish,
        allow_research_use=parsed.allow_research_use,
        allow_ai_training=parsed.allow_ai_training,
        allow_commercial_use=parsed.allow_commercial_use,
        notes=parsed.notes,
    )
    db.add(media)
    await db.flush()

    # Pending media must not be placed in the public search index before review.

    return MediaSubmissionDetail(**_build_media_detail(media).model_dump(), review_status="pending")


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