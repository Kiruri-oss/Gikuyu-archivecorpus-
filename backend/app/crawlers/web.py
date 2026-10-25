from urllib.parse import urlparse

from app.crawlers.base import BaseCrawler
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class WebCrawler(BaseCrawler):
    async def crawl(self, seed_urls: list[str], max_pages: int = 100) -> list[dict]:
        visited: set[str] = set()
        queue: list[str] = list(seed_urls)
        results: list[dict] = []
        max_pages = max(1, min(max_pages, 1000))

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            fetched = await self.fetch(url)
            if not fetched:
                continue
            html, final_url = fetched
            license_name = self.detect_open_license(html, final_url)
            if not license_name:
                logger.info("crawler.skipped_without_open_license", url=final_url)
                continue
            page = self.extract(html, final_url, license_name)
            if page is None:
                continue
            if page.language == "ki" and page.confidence >= settings.LANGUAGE_DETECTION_THRESHOLD:
                results.append({
                    "url": page.url,
                    "title": page.title,
                    "text": page.text,
                    "language": page.language,
                    "confidence": page.confidence,
                    "license": page.license,
                    "status": "pending",
                })
                logger.info("crawler.candidate_found", url=page.url, license=page.license)
            current_host = urlparse(final_url).hostname
            for link in page.links:
                if urlparse(link).hostname == current_host and link not in visited and len(queue) < max_pages * 3:
                    queue.append(link)
        return results
