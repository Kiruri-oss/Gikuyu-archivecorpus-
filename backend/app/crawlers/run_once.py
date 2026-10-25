"""Run one bounded corpus-hunter pass (suitable for a scheduled CI worker)."""
import asyncio

from app.crawlers.scheduler import crawl_scheduler


async def main() -> None:
    await crawl_scheduler.run_web_crawl()


if __name__ == "__main__":
    asyncio.run(main())
