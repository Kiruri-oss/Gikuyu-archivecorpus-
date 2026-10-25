from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger
from app.crawlers.web import WebCrawler

logger = get_logger(__name__)

# Only source roots whose open licensing can be checked page-by-page.
# No Bible, news, books, YouTube or social source is automatically archived.
SEED_URLS = [
    "https://ki.wikipedia.org/wiki/Main_Page",
    "https://ki.wiktionary.org/wiki/Main_Page",
    "https://www.wikidata.org/wiki/Wikidata:Main_Page",
]


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.web = WebCrawler()

    async def run_web_crawl(self) -> None:
        results = await self.web.crawl(SEED_URLS, max_pages=50)
        logger.info("scheduler.web_crawl_complete", found=len(results), archived=False,
                    message="Hunter returns candidates only; persistence and reviewer approval are separate steps.")

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.add_job(self.run_web_crawl, "interval", hours=12, id="web_crawl", replace_existing=True)
            self.scheduler.start()
            logger.info("scheduler.started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


crawl_scheduler = CrawlScheduler()
