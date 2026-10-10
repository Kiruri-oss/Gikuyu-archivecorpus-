from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.logging import get_logger
from app.crawlers.web import WebCrawler
from app.crawlers.youtube import YouTubeCrawler

logger = get_logger(__name__)

SEED_URLS = [
    "https://ki.wikipedia.org/wiki/Mũthũngũ",
    "https://ki.wiktionary.org/wiki/Mũthũngũ",
    "https://www.bible.com/bible/",
]


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.web = WebCrawler()
        self.youtube = YouTubeCrawler()

    async def run_web_crawl(self) -> None:
        results = await self.web.crawl(SEED_URLS, max_pages=50)
        logger.info("scheduler.web_crawl_complete", found=len(results))

    async def run_youtube_discovery(self) -> None:
        results = await self.youtube.discover(limit_per_query=10)
        logger.info("scheduler.youtube_complete", found=len(results))

    def start(self) -> None:
        self.scheduler.add_job(self.run_web_crawl, "interval", hours=12, id="web_crawl")
        self.scheduler.add_job(self.run_youtube_discovery, "interval", hours=6, id="youtube_discovery")
        self.scheduler.start()
        logger.info("scheduler.started")

    def stop(self) -> None:
        self.scheduler.shutdown(wait=False)


crawl_scheduler = CrawlScheduler()