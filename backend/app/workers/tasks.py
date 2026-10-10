import asyncio
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.media import Media
from app.models.source import Source
from app.services.indexing import search_index
from app.services.language_detector import language_detector
from app.services.transcription import transcription_service
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="transcribe_media", bind=True, max_retries=3)
def transcribe_media_task(self, media_id: str, local_path: str) -> dict:
    try:
        result = transcription_service.transcribe(local_path)
        if result["status"] != "ok":
            raise RuntimeError(f"transcription failed: {result['status']}")

        async def _persist():
            async with AsyncSessionLocal() as db:
                media = await db.get(Media, UUID(media_id))
                if not media:
                    return {"media_id": media_id, "status": "media_not_found"}
                media.notes = (media.notes or "") + f"\n[transcript] {result['text'][:5000]}"
                await db.commit()
                return {"media_id": media_id, "chars": len(result["text"])}

        return _run(_persist())
    except Exception as exc:
        logger.error("transcribe_task.failed", media_id=media_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="crawl_source", bind=True, max_retries=3)
def crawl_source_task(self, url: str) -> dict:
    from app.crawlers.web import WebCrawler

    async def _crawl():
        crawler = WebCrawler()
        results = await crawler.crawl([url], max_pages=1)
        if not results:
            return {"url": url, "found": 0}

        page = results[0]

        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(Source).where(Source.url == url))
            if existing.scalar_one_or_none():
                return {"url": url, "status": "already_exists"}

            from urllib.parse import urlparse
            source = Source(
                url=url,
                domain=urlparse(url).netloc,
                source_type="web",
                language_confidence=page["confidence"],
            )
            db.add(source)
            await db.commit()
            return {"url": url, "found": 1, "confidence": page["confidence"]}

    try:
        return _run(_crawl())
    except Exception as exc:
        logger.error("crawl_task.failed", url=url, error=str(exc))
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="index_media")
def index_media_task(media_id: str, title: str, speaker: str | None, dialect: str | None) -> dict:
    async def _index():
        await search_index.index_document("media", {
            "id": media_id,
            "title": title,
            "speaker": speaker or "",
            "dialect": dialect or "",
        })
        return {"media_id": media_id, "indexed": True}

    return _run(_index())