from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.source import Source


class DedupService:
    @staticmethod
    async def media_exists(db: AsyncSession, sha256: str) -> bool:
        result = await db.execute(select(Media.id).where(Media.sha256 == sha256))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def source_exists(db: AsyncSession, url: str) -> bool:
        result = await db.execute(select(Source.id).where(Source.url == url))
        return result.scalar_one_or_none() is not None


dedup_service = DedupService()