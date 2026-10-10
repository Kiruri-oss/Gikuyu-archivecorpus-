import csv
import io
import json
from typing import Iterable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.segment import Segment


class ExportService:
    @staticmethod
    async def export_jsonl(db: AsyncSession, dialect: str | None = None) -> Iterable[str]:
        stmt = select(Segment, Media).join(Media, Segment.media_id == Media.id)
        if dialect:
            stmt = stmt.where(Media.dialect == dialect)
        result = await db.execute(stmt)
        for segment, media in result.all():
            yield json.dumps({
                "id": str(segment.id),
                "media_id": str(media.id),
                "audio_key": media.file_key,
                "start": segment.start_seconds,
                "end": segment.end_seconds,
                "transcript": segment.transcript,
                "translation": segment.translation,
                "dialect": media.dialect,
                "speaker": media.speaker,
                "license": media.license,
            }, ensure_ascii=False) + "\n"

    @staticmethod
    async def export_csv(db: AsyncSession, dialect: str | None = None) -> str:
        stmt = select(Segment, Media).join(Media, Segment.media_id == Media.id)
        if dialect:
            stmt = stmt.where(Media.dialect == dialect)
        result = await db.execute(stmt)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "media_id", "start", "end", "transcript", "translation", "dialect", "speaker", "license"])
        for segment, media in result.all():
            writer.writerow([
                str(segment.id), str(media.id), segment.start_seconds, segment.end_seconds,
                segment.transcript or "", segment.translation or "",
                media.dialect or "", media.speaker or "", media.license or "",
            ])
        return buf.getvalue()


export_service = ExportService()