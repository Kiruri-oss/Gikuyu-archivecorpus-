from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class WebCrawler(BaseCrawler):
    def crawl_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            link = anchor.get("href")
            if not isinstance(link, str):
                continue
            from urllib.parse import urljoin
            absolute = urljoin(base_url, link)
            if self._is_public_http_url(absolute):
                links.append(absolute)
        return list(dict.fromkeys(links))[:100]

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
            current_host = urlparse(final_url).hostname

            # Unlicensed pages may be used only as navigation for discovery; their
            # body is never extracted into the corpus or written to the database.
            links = self.crawl_links(html, final_url)
            license_name = self.detect_open_license(html, final_url)
            if license_name:
                page = self.extract(html, final_url, license_name)
                if page and page.language == "ki" and page.confidence >= settings.LANGUAGE_DETECTION_THRESHOLD:
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
            else:
                logger.info("crawler.skipped_without_open_license", url=final_url)

            for link in links:
                if urlparse(link).hostname == current_host and link not in visited and len(queue) < max_pages * 3:
                    queue.append(link)
        return results
