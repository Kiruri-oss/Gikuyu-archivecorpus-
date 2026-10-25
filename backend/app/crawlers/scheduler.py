import hashlib
import json
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.crawlers.web import WebCrawler
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord

logger = get_logger(__name__)

# The hunter checks robots.txt and an explicit supported open licence before
# it extracts content. Video and news discovery remains permission-based.
SEED_URLS = [
    "https://ki.wikipedia.org/wiki/Main_Page",
    "https://ki.wiktionary.org/wiki/Main_Page",
    "https://www.wikidata.org/wiki/Wikidata:Main_Page",
]


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.web = WebCrawler()

    async def _archive_candidates(self, candidates: list[dict]) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in candidates:
                url = str(item["url"])
                existing = await db.execute(select(Source.id).where(Source.url == url))
                if existing.scalar_one_or_none():
                    continue

                body = str(item["text"]).strip()
                if not body:
                    continue
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                duplicate = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
                if duplicate.scalar_one_or_none():
                    continue

                source = Source(
                    url=url,
                    domain=url.split("/", 3)[2].lower(),
                    source_type=SourceType.WEB,
                    status=SourceStatus.PENDING,
                    license=str(item["license"]),
                    language_confidence=float(item["confidence"]),
                    fetched_at=datetime.now(timezone.utc),
                    raw_metadata=json.dumps({
                        "hunter": "gikuyu-open-source-hunter",
                        "language": item["language"],
                        "title": item["title"],
                        "license_detection": "automated_candidate_requires_review",
                    }, ensure_ascii=False),
                )
                db.add(source)
                await db.flush()
                record = TextRecord(
                    source_id=source.id,
                    source=source,
                    title=str(item["title"])[:500] or url,
                    body=body,
                    language_code="ki",
                    sha256=digest,
                    size_bytes=len(body.encode("utf-8")),
                    lang_score=float(item["confidence"]),
                    license=str(item["license"]),
                    # Pending source status prevents public display until review.
                    allow_public_display=True,
                    allow_research_use=True,
                    allow_ai_training=False,
                    allow_commercial_use=False,
                    notes="Automatically discovered candidate. Verify the source licence and content before approval.",
                )
                db.add(record)
                await db.flush()
                saved += 1
            await db.commit()
        return saved

    async def run_web_crawl(self) -> None:
        results = await self.web.crawl(SEED_URLS, max_pages=50)
        try:
            saved = await self._archive_candidates(results)
            logger.info("scheduler.web_crawl_complete", found=len(results), saved=saved, status="pending_review")
        except Exception as exc:
            logger.error("scheduler.archive_candidates_failed", found=len(results), error=str(exc))
            raise

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.add_job(self.run_web_crawl, "interval", hours=12, id="web_crawl", replace_existing=True)
            self.scheduler.start()
            logger.info("scheduler.started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


crawl_scheduler = CrawlScheduler()
