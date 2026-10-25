from urllib.parse import urlparse

from app.crawlers.base import BaseCrawler
from app.core.logging import get_logger
from app.crawlers.licensing import is_safe_http_url

logger = get_logger(__name__)


class WebCrawler(BaseCrawler):
    async def crawl(self, seed_urls: list[str], max_pages: int = 100) -> list[dict]:
        """Crawl only seeded hosts and return explicitly open-licensed Gĩkũyũ pages."""
        safe_seeds = [url for url in seed_urls if is_safe_http_url(url)]
        allowed_hosts = {urlparse(url).hostname for url in safe_seeds}
        visited: set[str] = set()
        queue: list[str] = list(safe_seeds)
        results: list[dict] = []
        page_budget = max(1, min(max_pages, 500))
        queued: set[str] = set(queue)

        while queue and len(visited) < page_budget:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            html = await self.fetch(url)
            if not html:
                continue

            page = self.extract(html, url)
            # A missing or unrecognised licence is not archived or added as a
            # corpus candidate. The crawler deliberately fails closed.
            if page and page.language == "ki" and page.confidence >= 0.55 and page.license:
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
                })
                logger.info("crawler.open_licensed_kikuyu_found", url=page.url, license=page.license, confidence=page.confidence)
            elif page is None:
                logger.info("crawler.page_not_ingested", url=url, reason="short_content_or_unparseable")
            elif not page.license:
                logger.info("crawler.discovery_only", url=url, reason="no_approved_open_license_detected")

            if page:
                for link in page.links:
                    host = urlparse(link).hostname
                    if host in allowed_hosts and link not in visited and link not in queued and len(queue) < page_budget * 3:
                        queue.append(link)
                        queued.add(link)

        logger.info("crawler.web_crawl_complete", visited=len(visited), licensed_kikuyu_records=len(results))
        return results
