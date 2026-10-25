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


class ExportService:
    @staticmethod
    async def export_jsonl(
        db: AsyncSession, dialect: str | None = None, purpose: ExportPurpose = "research"
    ) -> AsyncIterator[str]:
        stmt = (
            select(Segment, Media)
            .join(Media, Segment.media_id == Media.id)
            .join(Source, Media.source_id == Source.id)
            .where(Source.status == SourceStatus.APPROVED, Media.allow_public_display.is_(True), _permission_filter(Media, purpose))
        )
        if dialect:
            stmt = stmt.where(Media.dialect == dialect)
        result = await db.execute(stmt)
        for segment, media in result.all():
            yield json.dumps({
                "record_type": "transcript_segment",
                "id": str(segment.id),
                "media_id": str(media.id),
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
            select(TextRecord)
            .join(Source, TextRecord.source_id == Source.id)
            .where(Source.status == SourceStatus.APPROVED, TextRecord.allow_public_display.is_(True), _permission_filter(TextRecord, purpose))
        )
        if dialect:
            text_stmt = text_stmt.where(TextRecord.dialect == dialect)
        text_result = await db.execute(text_stmt)
        for record in text_result.scalars().all():
            yield json.dumps({
                "record_type": "text",
                "id": str(record.id),
                "title": record.title,
                "text": record.body,
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
        db: AsyncSession, dialect: str | None = None, purpose: ExportPurpose = "research"
    ) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "record_type", "id", "media_id", "title", "text", "start", "end",
            "transcript", "translation", "language_code", "dialect", "speaker",
            "author", "year", "genre", "license", "allow_research_use",
            "allow_ai_training", "allow_commercial_use",
        ])

        media_stmt = (
            select(Segment, Media)
            .join(Media, Segment.media_id == Media.id)
            .join(Source, Media.source_id == Source.id)
            .where(Source.status == SourceStatus.APPROVED, Media.allow_public_display.is_(True), _permission_filter(Media, purpose))
        )
        if dialect:
            media_stmt = media_stmt.where(Media.dialect == dialect)
        media_result = await db.execute(media_stmt)
        for segment, media in media_result.all():
            writer.writerow([
                "transcript_segment", str(segment.id), str(media.id), media.title, "",
                segment.start_seconds, segment.end_seconds, segment.transcript or "",
                segment.translation or "", media.dialect or "", media.dialect or "",
                media.speaker or "", "", "", media.genre or "", media.license or "",
                media.allow_research_use, media.allow_ai_training, media.allow_commercial_use,
            ])

        text_stmt = (
            select(TextRecord)
            .join(Source, TextRecord.source_id == Source.id)
            .where(Source.status == SourceStatus.APPROVED, TextRecord.allow_public_display.is_(True), _permission_filter(TextRecord, purpose))
        )
        if dialect:
            text_stmt = text_stmt.where(TextRecord.dialect == dialect)
        text_result = await db.execute(text_stmt)
        for record in text_result.scalars().all():
            writer.writerow([
                "text", str(record.id), "", record.title, record.body, "", "", "", "",
                record.language_code, record.dialect or "", "", record.author or "",
                record.year or "", record.genre or "", record.license,
                record.allow_research_use, record.allow_ai_training, record.allow_commercial_use,
            ])
        return buf.getvalue()


export_service = ExportService()
