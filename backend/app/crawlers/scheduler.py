import hashlib
import json
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.crawlers.web import WebCrawler
from app.db.session import AsyncSessionLocal
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord

logger = get_logger(__name__)
settings = get_settings()

# Explicit seed hosts keep the hunter bounded and operator-controlled. Add
# additional public repositories through CRAWLER_SEED_URLS after checking them.
SEED_URLS = [
    item.strip()
    for item in settings.CRAWLER_SEED_URLS.split(",")
    if item.strip()
]


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.web = WebCrawler()

    async def _archive_verified_pages(self, results: list[dict]) -> tuple[int, int]:
        created = 0
        duplicates = 0
        async with AsyncSessionLocal() as db:
            for item in results:
                url = item["url"]
                exists = await db.execute(select(Source.id).where(Source.url == url))
                if exists.scalar_one_or_none():
                    duplicates += 1
                    continue

                body = item["text"].replace("\\r\\n", "\\n").strip()
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                body_exists = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
                if body_exists.scalar_one_or_none():
                    duplicates += 1
                    continue

                source = Source(
                    url=url,
                    domain=url.split("/", 3)[2].lower(),
                    source_type=SourceType.WEB,
                    status=SourceStatus.PENDING,
                    license=item["license"],
                    language_confidence=item["confidence"],
                    raw_metadata=json.dumps({
                        "discovery_method": "robots-respecting-open-license-hunter",
                        "date_found": datetime.now(timezone.utc).isoformat(),
                        "license_verified": True,
                        "license_url": item.get("license_url"),
                        "source_url": url,
                        "review_required": True,
                    }, ensure_ascii=False),
                )
                db.add(source)
                await db.flush()
                record = TextRecord(
                    source_id=source.id,
                    title=item.get("title") or url,
                    body=body,
                    language_code="ki",
                    sha256=digest,
                    size_bytes=len(body.encode("utf-8")),
                    lang_score=item["confidence"],
                    license=item["license"],
                    allow_public_display=True,
                    allow_research_use=bool(item.get("permits_research")),
                    allow_ai_training=bool(item.get("permits_ai_training")),
                    allow_commercial_use=bool(item.get("permits_commercial_use")),
                    notes="Automatically discovered. Source remains pending human review before public listing.",
                )
                db.add(record)
                try:
                    await db.flush()
                    await db.commit()
                    created += 1
                except IntegrityError:
                    await db.rollback()
                    duplicates += 1
            return created, duplicates

    async def run_web_crawl(self) -> None:
        if not SEED_URLS:
            logger.warning("scheduler.web_crawl_skipped", reason="no_seed_urls_configured")
            return
        results = await self.web.crawl(SEED_URLS, max_pages=100)
        created, duplicates = await self._archive_verified_pages(results)
        logger.info(
            "scheduler.web_crawl_complete",
            discovered=len(results),
            archived_pending_review=created,
            duplicates=duplicates,
        )

    def start(self) -> None:
        if not self.scheduler.get_job("web_crawl"):
            self.scheduler.add_job(self.run_web_crawl, "interval", hours=12, id="web_crawl", max_instances=1, coalesce=True)
        self.scheduler.start()
        logger.info("scheduler.started", seed_hosts=len(SEED_URLS))

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


crawl_scheduler = CrawlScheduler()
