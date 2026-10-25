import hashlib
import json
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.crawlers.web import WebCrawler
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord

logger = get_logger(__name__)
settings = get_settings()
SEED_URLS = [item.strip() for item in settings.CRAWLER_SEED_URLS.split(",") if item.strip()]


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.web = WebCrawler()
        self.last_run: dict[str, object] = {"status": "never_run"}

    async def _archive_candidates(self, candidates: list[dict]) -> dict[str, int]:
        saved_sources = 0
        saved_texts = 0
        duplicate_texts = 0
        async with AsyncSessionLocal() as db:
            for item in candidates:
                url = str(item["url"])
                existing = await db.execute(select(Source.id).where(Source.url == url))
                if existing.scalar_one_or_none():
                    continue

                body = str(item.get("text") or "").strip()
                archive_content = bool(item.get("archive_content")) and bool(body)
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest() if archive_content else None
                duplicate = False
                if digest:
                    duplicate_result = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
                    duplicate = duplicate_result.scalar_one_or_none() is not None
                    duplicate_texts += int(duplicate)

                rights_state = "explicit_open_licence_detected" if item.get("license_url") else (
                    "licence_label_detected_needs_review"
                    if item.get("license") not in (None, "", "UNVERIFIED")
                    else "rights_not_detected"
                )
                source = Source(
                    url=url,
                    domain=url.split("/", 3)[2].lower(),
                    source_type=SourceType.WEB,
                    status=SourceStatus.PENDING,
                    license=str(item.get("license") or "UNVERIFIED")[:100],
                    language_confidence=float(item.get("confidence") or 0.0),
                    fetched_at=datetime.now(timezone.utc),
                    raw_metadata=json.dumps({
                        "hunter": "gikuyu-open-source-hunter",
                        "language": item.get("language", "unknown"),
                        "title": item.get("title", url),
                        "license_url": item.get("license_url"),
                        "rights_state": rights_state,
                        "content_archived": bool(archive_content and not duplicate),
                        "review_required": True,
                    }, ensure_ascii=False),
                )
                db.add(source)
                await db.flush()
                saved_sources += 1

                # Keep a provenance record for every discovered source, but never
                # duplicate identical text or treat an unverified licence as reuse
                # permission. Pending records are not publicly searchable/exported.
                if not archive_content or duplicate:
                    continue

                record = TextRecord(
                    source_id=source.id,
                    source=source,
                    title=str(item.get("title") or url)[:500],
                    body=body,
                    language_code="ki",
                    sha256=str(digest),
                    size_bytes=len(body.encode("utf-8")),
                    lang_score=float(item.get("confidence") or 0.0),
                    license=str(item.get("license") or "UNVERIFIED")[:100],
                    allow_public_display=False,
                    allow_research_use=bool(item.get("permits_research")),
                    allow_ai_training=bool(item.get("permits_ai_training")),
                    allow_commercial_use=bool(item.get("permits_commercial_use")),
                    notes="Hunter candidate; verify language, source rights and permitted uses before approval.",
                )
                db.add(record)
                await db.flush()
                saved_texts += 1

            await db.commit()
        return {
            "sources_saved": saved_sources,
            "texts_saved": saved_texts,
            "duplicate_texts": duplicate_texts,
        }

    async def run_web_crawl(self, max_pages: int | None = None) -> dict[str, object]:
        started_at = datetime.now(timezone.utc).isoformat()
        self.last_run = {"status": "running", "started_at": started_at}
        try:
            results = await self.web.crawl(
                SEED_URLS,
                max_pages=max_pages or settings.CRAWLER_MAX_PAGES,
                max_domains=settings.CRAWLER_MAX_DOMAINS,
                max_pages_per_domain=settings.CRAWLER_MAX_PAGES_PER_DOMAIN,
            )
            counts = await self._archive_candidates(results)
            self.last_run = {
                "status": "completed",
                "started_at": started_at,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "pages_discovered": len(results),
                **counts,
            }
            logger.info("scheduler.web_crawl_complete", **self.last_run)
            return self.last_run
        except Exception as exc:
            self.last_run = {
                "status": "failed",
                "started_at": started_at,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc)[:1000],
            }
            logger.error("scheduler.web_crawl_failed", error=str(exc))
            raise

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.add_job(
                self.run_web_crawl,
                "interval",
                hours=12,
                id="web_crawl",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            self.scheduler.start()
            logger.info("scheduler.started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


crawl_scheduler = CrawlScheduler()
