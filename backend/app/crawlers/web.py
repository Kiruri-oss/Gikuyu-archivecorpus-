from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler
from app.crawlers.licensing import canonicalize_url, is_safe_http_url
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class WebCrawler(BaseCrawler):
    def crawl_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            link = anchor.get("href")
            if not isinstance(link, str):
                continue
            absolute = urljoin(base_url, link)
            if is_safe_http_url(absolute):
                links.append(canonicalize_url(absolute))
        return list(dict.fromkeys(links))[:100]

    async def crawl(self, seed_urls: list[str], max_pages: int = 100) -> list[dict]:
        safe_seeds = [canonicalize_url(url) for url in seed_urls if is_safe_http_url(url)]
        visited: set[str] = set()
        queued: set[str] = set(safe_seeds)
        queue: list[str] = list(safe_seeds)
        results: list[dict] = []
        page_budget = max(1, min(max_pages, 1000))

        while queue and len(visited) < page_budget:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            fetched = await self.fetch(url)
            if not fetched:
                continue
            html, final_url = fetched
            final_url = canonicalize_url(final_url)
            current_host = urlparse(final_url).hostname

            # Unlicensed pages are navigation-only: they can reveal links, but
            # their content is never extracted into or stored in the corpus.
            links = self.crawl_links(html, final_url)
            licence = self.detect_open_license(html, final_url)
            if licence:
                page = self.extract(html, final_url, licence)
                if page and page.language == "ki" and page.confidence >= settings.LANGUAGE_DETECTION_THRESHOLD:
                    results.append({
                        "url": page.url,
                        "title": page.title,
                        "text": page.text,
                        "language": page.language,
                        "confidence": page.confidence,
                        "license": page.license,
                        "license_url": page.license_url,
                        "permits_research": page.permits_research,
                        "permits_ai_training": page.permits_ai_training,
                        "permits_commercial_use": page.permits_commercial_use,
                        "status": "pending",
                    })
                    logger.info("crawler.candidate_found", url=page.url, license=page.license)
            else:
                logger.info("crawler.skipped_without_open_license", url=final_url)

            for link in links:
                if urlparse(link).hostname == current_host and link not in visited and link not in queued and len(queue) < page_budget * 3:
                    queue.append(link)
                    queued.add(link)
        logger.info("crawler.crawl_complete", visited=len(visited), candidates=len(results))
        return results
