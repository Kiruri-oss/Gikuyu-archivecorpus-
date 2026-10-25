import asyncio
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
from app.services.indexing import search_index

logger = get_logger(__name__)
settings = get_settings()
SEED_URLS = [item.strip() for item in settings.CRAWLER_SEED_URLS.split(",") if item.strip()]


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.web = WebCrawler()
        self.last_run: dict[str, object] = {"status": "never_run"}
        self._run_lock = asyncio.Lock()

    async def _archive_candidates(self, candidates: list[dict]) -> int:
        saved = 0
        documents_to_index: list[dict] = []
        async with AsyncSessionLocal() as db:
            for item in candidates:
                url = str(item["url"])
                existing = await db.execute(select(Source.id).where(Source.url == url))
                if existing.scalar_one_or_none():
                    continue
                licence = str(item.get("license") or "UNKNOWN — licence not stated")
                identified_open_licence = item.get("rights_state") == "identified_open_licence"
                body = str(item.get("text") or "").strip()
                # A page with unclear or restrictive rights is still recorded as
                # a discovery lead, but its protected body is never stored or indexed.
                if identified_open_licence and not body:
                    continue
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest() if body else None
                if digest:
                    duplicate = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
                    if duplicate.scalar_one_or_none():
                        continue
                source = Source(
                    url=url,
                    domain=url.split("/", 3)[2].lower(),
                    source_type=SourceType.WEB,
                    status=SourceStatus.APPROVED if identified_open_licence else SourceStatus.PENDING,
                    license=licence[:100],
                    language_confidence=float(item["confidence"]),
                    fetched_at=datetime.now(timezone.utc),
                    raw_metadata=json.dumps({
                        "hunter": "gikuyu-open-web-hunter",
                        "language": "ki",
                        "title": str(item["title"]),
                        "license_url": item.get("license_url"),
                        "license_detection": "explicit_open_licence" if identified_open_licence else "not_detected",
                        "rights_state": item.get("rights_state", "unknown_pending_rights_review"),
                        "collection_mode": "full_text" if identified_open_licence else "metadata_and_source_link_only",
                        "review_required": not identified_open_licence,
                        "source_url_is_reference_not_archive_content": not identified_open_licence,
                    }, ensure_ascii=False),
                )
                db.add(source)
                await db.flush()
                saved += 1
                if not identified_open_licence:
                    # Store source provenance only. No copyrighted page text,
                    # scraped excerpt, transcript, or searchable body is retained.
                    continue
                record = TextRecord(
                    source_id=source.id,
                    source=source,
                    title=str(item["title"])[:500] or url,
                    body=body,
                    language_code="ki",
                    sha256=digest,
                    size_bytes=len(body.encode("utf-8")),
                    lang_score=float(item["confidence"]),
                    license=licence[:100],
                    allow_public_display=True,
                    allow_research_use=bool(item.get("permits_research", False)),
                    allow_ai_training=bool(item.get("permits_ai_training", False)),
                    allow_commercial_use=bool(item.get("permits_commercial_use", False)),
                    notes=(
                        "Automatically discovered Gĩkũyũ material. Unknown rights do not "
                        "grant AI-training or commercial reuse permission. Valid rights "
                        "requests are handled through the takedown workflow."
                    ),
                )
                db.add(record)
                await db.flush()
                documents_to_index.append({
                    "id": str(record.id),
                    "title": record.title,
                    "body": record.body,
                    "language_code": "ki",
                    "dialect": record.dialect or "",
                    "genre": record.genre or "",
                    "license": record.license,
                    "source_url": source.url,
                    "allow_ai_training": record.allow_ai_training,
                    "allow_commercial_use": record.allow_commercial_use,
                })
            await db.commit()
        indexed = 0
        for document in documents_to_index:
            try:
                await search_index.index_document("texts", document)
                indexed += 1
            except Exception as exc:
                logger.warning("scheduler.text_index_failed", record_id=document["id"], error=str(exc))
        logger.info("scheduler.archive_index_summary", saved=saved, indexed=indexed)
        return saved

    async def run_web_crawl(self, max_pages: int = 500) -> dict[str, object]:
        if self._run_lock.locked():
            raise RuntimeError("A Gĩkũyũ hunter run is already in progress.")
        async with self._run_lock:
            started_at = datetime.now(timezone.utc).isoformat()
            self.last_run = {"status": "running", "started_at": started_at, "max_pages": max_pages}
            try:
                results = await self.web.crawl(SEED_URLS, max_pages=max_pages)
                saved = await self._archive_candidates(results)
                completed = {
                    "status": "completed",
                    "started_at": started_at,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "seed_count": len(SEED_URLS),
                    "max_pages": max_pages,
                    "found": len(results),
                    "saved": saved,
                }
                self.last_run = completed
                logger.info(
                    "scheduler.web_crawl_complete",
                    found=len(results),
                    saved=saved,
                    status="notice_and_takedown",
                )
                return completed
            except Exception as exc:
                self.last_run = {
                    "status": "failed",
                    "started_at": started_at,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "max_pages": max_pages,
                    "error": str(exc),
                }
                logger.error("scheduler.web_crawl_failed", error=str(exc), max_pages=max_pages)
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
