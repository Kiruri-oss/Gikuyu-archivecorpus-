from app.crawlers.base import BaseCrawler
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebCrawler(BaseCrawler):
    async def crawl(self, seed_urls: list[str], max_pages: int = 100) -> list[dict]:
        visited: set[str] = set()
        queue: list[str] = list(seed_urls)
        results: list[dict] = []

        while queue and len(results) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            html = await self.fetch(url)
            if not html:
                continue

            page = self.extract(html, url)
            if page is None:
                continue
            if page.language == "ki" and page.confidence >= 0.55:
                results.append({
                    "url": page.url,
                    "title": page.title,
                    "text": page.text,
                    "language": page.language,
                    "confidence": page.confidence,
                })
                logger.info("crawler.kikuyu_found", url=page.url, confidence=page.confidence)

            for link in page.links:
                if link not in visited and len(queue) < max_pages * 3:
                    queue.append(link)

        return results