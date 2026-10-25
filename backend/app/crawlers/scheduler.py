import asyncio
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.crawlers.web import WebCrawler
from app.crawlers.youtube import YouTubeCrawler
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
        self.youtube = YouTubeCrawler()
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
                body = str(item["text"]).strip()
                if not body:
                    continue
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                duplicate = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
                if duplicate.scalar_one_or_none():
                    continue

                licence = str(item.get("license") or "UNKNOWN — licence not stated")
                identified_open_licence = item.get("rights_state") == "identified_open_licence"
                source = Source(
                    url=url,
                    domain=url.split("/", 3)[2].lower(),
                    source_type=SourceType.WEB,
                    # This is a notice-and-takedown corpus: collection is not blocked
                    # merely because a site lacks machine-readable licence metadata.
                    status=SourceStatus.APPROVED,
                    license=licence[:100],
                    language_confidence=float(item["confidence"]),
                    fetched_at=datetime.now(timezone.utc),
                    raw_metadata=json.dumps({
                        "hunter": "gikuyu-open-web-hunter",
                        "language": "ki",
                        "title": str(item["title"]),
                        "license_url": item.get("license_url"),
                        "license_detection": "explicit_open_licence" if identified_open_licence else "not_detected",
                        "rights_state": item.get("rights_state", "unknown_pending_rights_request"),
                        "review_required": not identified_open_licence,
                        "collection_model": "notice_and_takedown",
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
                    license=licence[:100],
                    allow_public_display=True,
                    allow_research_use=bool(item.get("permits_research", False)),
                    allow_ai_training=bool(item.get("permits_ai_training", False)),
                    allow_commercial_use=bool(item.get("permits_commercial_use", False)),
                    notes=(
                        "Automatically discovered Gĩkũyũ material. Unknown rights do not "
                        "grant AI-training or commercial reuse permission. A rights request "
                        "can trigger removal through the takedown workflow."
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
                saved += 1
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

    async def _archive_youtube_candidates(self, candidates: list[dict]) -> int:
        """Persist discovered public video metadata for later language/content review."""
        saved = 0
        seen_urls: set[str] = set()
        async with AsyncSessionLocal() as db:
            for item in candidates:
                url = str(item.get("url") or "").strip()
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                if not url.startswith("https://www.youtube.com/watch?v="):
                    continue
                existing = await db.execute(select(Source.id).where(Source.url == url))
                if existing.scalar_one_or_none():
                    continue

                metadata = {
                    "hunter": "gikuyu-youtube-discovery",
                    "language": "ki",
                    "discovery_query": str(item.get("query") or ""),
                    "title": str(item.get("title") or ""),
                    "channel": str(item.get("channel") or ""),
                    "duration_seconds": item.get("duration"),
                    "rights_state": "unknown_pending_rights_request",
                    "content_state": "metadata_only",
                    "review_required": True,
                }
                db.add(Source(
                    url=url,
                    domain=(urlparse(url).netloc or "www.youtube.com").lower(),
                    source_type=SourceType.YOUTUBE,
                    status=SourceStatus.PENDING,
                    license="UNKNOWN — not stated",
                    fetched_at=datetime.now(timezone.utc),
                    raw_metadata=json.dumps(metadata, ensure_ascii=False),
                ))
                saved += 1
            if saved:
                await db.commit()
        logger.info("scheduler.youtube_sources_saved", saved=saved, discovered=len(candidates))
        return saved

    async def run_web_crawl(self, max_pages: int = 500) -> dict[str, object]:
        if self._run_lock.locked():
            raise RuntimeError("A hunter run is already in progress.")
        async with self._run_lock:
            started_at = datetime.now(timezone.utc).isoformat()
            page_budget = max(1, min(max_pages, 1000))
            self.last_run = {"status": "running", "started_at": started_at, "page_budget": page_budget}
            try:
                results = await self.web.crawl(SEED_URLS, max_pages=page_budget)
                saved = await self._archive_candidates(results)
                youtube_sources_saved = 0
                try:
                    youtube_candidates = await self.youtube.discover(limit_per_query=25)
                    youtube_sources_saved = await self._archive_youtube_candidates(youtube_candidates)
                except Exception as exc:
                    # Video discovery must not discard a successful web-crawl run.
                    logger.warning("scheduler.youtube_discovery_failed", error=str(exc))
                self.last_run = {
                    "status": "completed",
                    "started_at": started_at,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "pages_discovered": len(results),
                    "records_saved": saved,
                    "video_sources_saved": youtube_sources_saved,
                    "page_budget": page_budget,
                }
                logger.info("scheduler.web_crawl_complete", **self.last_run, collection_model="notice_and_takedown")
                return self.last_run
            except Exception as exc:
                self.last_run = {
                    "status": "failed",
                    "started_at": started_at,
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "page_budget": page_budget,
                    "error": str(exc)[:1000],
                }
                logger.error("scheduler.archive_candidates_failed", **self.last_run)
                raise

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.add_job(
                self.run_web_crawl,
                "interval",
                hours=6,
                id="web_crawl",
                replace_existing=True,
                next_run_time=datetime.now(timezone.utc),
                max_instances=1,
                coalesce=True,
            )
            self.scheduler.start()
            logger.info("scheduler.started", seed_count=len(SEED_URLS), max_pages=500, interval_hours=6)

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


crawl_scheduler = CrawlScheduler()
