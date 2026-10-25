import csv
import io
import json
from typing import AsyncIterator, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.segment import Segment
from app.models.source import Source, SourceStatus
from app.models.text_record import TextRecord

ExportPurpose = Literal["research", "ai_training", "commercial"]


def _permission_filter(model, purpose: ExportPurpose):
    if purpose == "ai_training":
        return model.allow_ai_training.is_(True)
    if purpose == "commercial":
        return model.allow_commercial_use.is_(True)
    return model.allow_research_use.is_(True)


def _license_filter(model, license_filter: str | None):
    if not license_filter or license_filter == "all":
        return None
    aliases = {
        "CC0": ["CC0", "CC0 1.0"],
        "CC-BY": ["CC-BY", "CC BY", "CC BY 4.0", "CC-BY-4.0", "CC-BY-3.0", "CC BY 3.0"],
        "PUBLIC-DOMAIN": ["PUBLIC-DOMAIN", "Public domain", "public domain"],
    }
    return model.license.in_(aliases[license_filter]) if license_filter in aliases else model.license == license_filter


def _license_url(source: Source) -> str:
    try:
        metadata = json.loads(source.raw_metadata or "{}")
        return str(metadata.get("license_url") or "")
    except (TypeError, ValueError):
        return ""


def _source_metadata(source: Source) -> dict[str, str]:
    found_at = source.fetched_at or source.created_at
    return {
        "source_url": source.url,
        "source_found_at": found_at.isoformat() if found_at else "",
        "license_url": _license_url(source),
    }


class ExportService:
    @staticmethod
    async def export_jsonl(
        db: AsyncSession,
        dialect: str | None = None,
        purpose: ExportPurpose = "research",
        license_filter: str | None = None,
    ) -> AsyncIterator[str]:
        stmt = (
            select(Segment, Media, Source)
            .join(Media, Segment.media_id == Media.id)
            .join(Source, Media.source_id == Source.id)
            .where(
                Source.status == SourceStatus.APPROVED,
                Media.allow_public_display.is_(True),
                _permission_filter(Media, purpose),
            )
        )
        if dialect:
            stmt = stmt.where(Media.dialect == dialect)
        media_license_clause = _license_filter(Media, license_filter)
        if media_license_clause is not None:
            stmt = stmt.where(media_license_clause)
        result = await db.execute(stmt)
        for segment, media, source in result.all():
            yield json.dumps({
                "record_type": "transcript_segment",
                "id": str(segment.id),
                "media_id": str(media.id),
                **_source_metadata(source),
                "audio_key": media.file_key,
                "start": segment.start_seconds,
                "end": segment.end_seconds,
                "transcript": segment.transcript,
                "translation": segment.translation,
                "language_code": media.dialect,
                "dialect": media.dialect,
                "speaker": media.speaker,
                "license": media.license,
                "allow_research_use": media.allow_research_use,
                "allow_ai_training": media.allow_ai_training,
                "allow_commercial_use": media.allow_commercial_use,
            }, ensure_ascii=False) + "\n"

        text_stmt = (
            select(TextRecord, Source)
            .join(Source, TextRecord.source_id == Source.id)
            .where(
                Source.status == SourceStatus.APPROVED,
                TextRecord.language_code == "ki",
                TextRecord.allow_public_display.is_(True),
                _permission_filter(TextRecord, purpose),
            )
        )
        if dialect:
            text_stmt = text_stmt.where(TextRecord.dialect == dialect)
        text_license_clause = _license_filter(TextRecord, license_filter)
        if text_license_clause is not None:
            text_stmt = text_stmt.where(text_license_clause)
        text_result = await db.execute(text_stmt)
        for record, source in text_result.all():
            yield json.dumps({
                "record_type": "text",
                "id": str(record.id),
                "title": record.title,
                "text": record.body,
                **_source_metadata(source),
                "language_code": record.language_code,
                "dialect": record.dialect,
                "genre": record.genre,
                "author": record.author,
                "year": record.year,
                "license": record.license,
                "allow_research_use": record.allow_research_use,
                "allow_ai_training": record.allow_ai_training,
                "allow_commercial_use": record.allow_commercial_use,
            }, ensure_ascii=False) + "\n"

    @staticmethod
    async def export_csv(
        db: AsyncSession,
        dialect: str | None = None,
        purpose: ExportPurpose = "research",
        license_filter: str | None = None,
    ) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "record_type", "id", "media_id", "source_url", "source_found_at", "license_url",
            "title", "text", "start", "end", "transcript", "translation", "language_code",
            "dialect", "speaker", "author", "year", "genre", "license", "allow_research_use",
            "allow_ai_training", "allow_commercial_use",
        ])

        media_stmt = (
            select(Segment, Media, Source)
            .join(Media, Segment.media_id == Media.id)
            .join(Source, Media.source_id == Source.id)
            .where(
                Source.status == SourceStatus.APPROVED,
                Media.allow_public_display.is_(True),
                _permission_filter(Media, purpose),
            )
        )
        if dialect:
            media_stmt = media_stmt.where(Media.dialect == dialect)
        media_license_clause = _license_filter(Media, license_filter)
        if media_license_clause is not None:
            media_stmt = media_stmt.where(media_license_clause)
        media_result = await db.execute(media_stmt)
        for segment, media, source in media_result.all():
            provenance = _source_metadata(source)
            writer.writerow([
                "transcript_segment", str(segment.id), str(media.id), provenance["source_url"],
                provenance["source_found_at"], provenance["license_url"], media.title, "",
                segment.start_seconds, segment.end_seconds, segment.transcript or "",
                segment.translation or "", media.dialect or "", media.dialect or "",
                media.speaker or "", "", "", media.genre or "", media.license or "",
                media.allow_research_use, media.allow_ai_training, media.allow_commercial_use,
            ])

        text_stmt = (
            select(TextRecord, Source)
            .join(Source, TextRecord.source_id == Source.id)
            .where(
                Source.status == SourceStatus.APPROVED,
                TextRecord.language_code == "ki",
                TextRecord.allow_public_display.is_(True),
                _permission_filter(TextRecord, purpose),
            )
        )
        if dialect:
            text_stmt = text_stmt.where(TextRecord.dialect == dialect)
        text_license_clause = _license_filter(TextRecord, license_filter)
        if text_license_clause is not None:
            text_stmt = text_stmt.where(text_license_clause)
        text_result = await db.execute(text_stmt)
        for record, source in text_result.all():
            provenance = _source_metadata(source)
            writer.writerow([
                "text", str(record.id), "", provenance["source_url"], provenance["source_found_at"],
                provenance["license_url"], record.title, record.body, "", "", "", "",
                record.language_code, record.dialect or "", "", record.author or "",
                record.year or "", record.genre or "", record.license,
                record.allow_research_use, record.allow_ai_training, record.allow_commercial_use,
            ])
        return buf.getvalue()


export_service = ExportService()
