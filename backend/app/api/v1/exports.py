import asyncio
import json
import os
import tempfile
import zipfile
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse, PlainTextResponse
from starlette.background import BackgroundTask
from sqlalchemy import func, or_, select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.deps import DbSession, ResearcherUser
from app.models.media import Media
from app.models.source import Source, SourceStatus
from app.services.export import export_service, LicenseFilter, _permission_filter, _license_filter
from app.services.storage import storage_service

router = APIRouter(prefix="/exports", tags=["exports"])
settings = get_settings()
logger = get_logger(__name__)
MAX_WAV_EXPORT_FILES = 100
MAX_WAV_EXPORT_BYTES = 512 * 1024 * 1024


def _build_wav_zip(records: list[dict]) -> str:
    """Build a bounded ZIP containing permitted WAV originals and a provenance manifest."""
    fd, zip_path = tempfile.mkstemp(prefix="gikuyu-corpus-audio-", suffix=".zip")
    os.close(fd)
    manifest = {
        "language_code": "ki",
        "format": "WAV",
        "audio_files_are_originals": True,
        "records": [],
        "skipped": [],
    }
    total_bytes = 0
    try:
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_STORED) as archive:
            for record in records:
                declared_size = int(record.get("size_bytes") or 0)
                if declared_size and declared_size > MAX_WAV_EXPORT_BYTES:
                    manifest["skipped"].append({"id": record["id"], "reason": "file exceeds export size limit"})
                    continue
                if declared_size and total_bytes + declared_size > MAX_WAV_EXPORT_BYTES:
                    manifest["skipped"].append({"id": record["id"], "reason": "export size limit reached"})
                    continue

                audio_fd, audio_path = tempfile.mkstemp(prefix="gikuyu-audio-", suffix=".wav")
                os.close(audio_fd)
                try:
                    with open(audio_path, "wb") as audio_file:
                        storage_service.download_fileobj(settings.S3_BUCKET_AUDIO, record["file_key"], audio_file)
                    actual_size = os.path.getsize(audio_path)
                    if actual_size > MAX_WAV_EXPORT_BYTES or total_bytes + actual_size > MAX_WAV_EXPORT_BYTES:
                        manifest["skipped"].append({"id": record["id"], "reason": "export size limit reached"})
                        continue
                    archive.write(audio_path, arcname=f"audio/{record['id']}.wav")
                    total_bytes += actual_size
                    manifest["records"].append({
                        "id": record["id"],
                        "title": record["title"],
                        "source_url": record["source_url"],
                        "license": record["license"],
                        "sha256": record["sha256"],
                        "size_bytes": actual_size,
                        "dialect": record.get("dialect"),
                        "speaker": record.get("speaker"),
                        "allow_research_use": record["allow_research_use"],
                        "allow_ai_training": record["allow_ai_training"],
                        "allow_commercial_use": record["allow_commercial_use"],
                    })
                except Exception as exc:
                    logger.warning("export.wav_download_failed", media_id=record["id"], error=str(exc))
                    manifest["skipped"].append({"id": record["id"], "reason": "object storage download failed"})
                finally:
                    try:
                        os.unlink(audio_path)
                    except FileNotFoundError:
                        pass
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        return zip_path
    except Exception:
        try:
            os.unlink(zip_path)
        except FileNotFoundError:
            pass
        raise


@router.get("/audio")
async def export_wav_audio(
    db: DbSession,
    _: ResearcherUser,
    dialect: str | None = None,
    purpose: Literal["research", "ai_training", "commercial"] = Query(default="ai_training"),
    license_filter: LicenseFilter = Query(default="all_verified"),
    limit: int = Query(default=MAX_WAV_EXPORT_FILES, ge=1, le=MAX_WAV_EXPORT_FILES),
    offset: int = Query(default=0, ge=0),
) -> FileResponse:
    wav_type = or_(
        func.lower(Media.mime_type).like("audio/wav%"),
        func.lower(Media.mime_type).like("audio/x-wav%"),
        func.lower(Media.mime_type).like("audio/wave%"),
        func.lower(Media.mime_type).like("audio/vnd.wave%"),
    )
    stmt = (
        select(Media, Source)
        .join(Source, Media.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            Media.language_code == "ki",
            Media.allow_public_display.is_(True),
            _permission_filter(Media, purpose),
            _license_filter(Media, license_filter),
            wav_type,
        )
        .order_by(Media.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if dialect:
        stmt = stmt.where(Media.dialect == dialect)
    result = await db.execute(stmt)
    records = [
        {
            "id": str(media.id),
            "title": media.title,
            "file_key": media.file_key,
            "size_bytes": media.size_bytes,
            "source_url": source.url,
            "license": media.license,
            "sha256": media.sha256,
            "dialect": media.dialect,
            "speaker": media.speaker,
            "allow_research_use": media.allow_research_use,
            "allow_ai_training": media.allow_ai_training,
            "allow_commercial_use": media.allow_commercial_use,
        }
        for media, source in result.all()
    ]
    if not records:
        raise HTTPException(status_code=404, detail="No permitted WAV recordings match these export filters.")
    zip_path = await asyncio.to_thread(_build_wav_zip, records)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"gikuyu-corpus-audio-{purpose}.zip",
        background=BackgroundTask(os.unlink, zip_path),
    )


@router.get("/jsonl")
async def export_jsonl(
    db: DbSession,
    _: ResearcherUser,
    dialect: str | None = None,
    purpose: Literal["research", "ai_training", "commercial"] = Query(default="research"),
    license_filter: LicenseFilter = Query(default="all_verified"),
) -> StreamingResponse:
    async def stream():
        async for line in export_service.export_jsonl(db, dialect, purpose, license_filter):
            yield line
    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="gikuyu-archive-{purpose}.jsonl"'},
    )


@router.get("/csv")
async def export_csv(
    db: DbSession,
    _: ResearcherUser,
    dialect: str | None = None,
    purpose: Literal["research", "ai_training", "commercial"] = Query(default="research"),
    license_filter: LicenseFilter = Query(default="all_verified"),
) -> PlainTextResponse:
    csv_data = await export_service.export_csv(db, dialect, purpose, license_filter)
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="gikuyu-archive-{purpose}.csv"'},
    )
