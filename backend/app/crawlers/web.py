from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler
from app.crawlers.licensing import canonicalize_url, is_safe_http_url
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
RELEVANT_LINK_TERMS = (
    "gikuyu", "gĩkũyũ", "kikuyu", "kik", "oral-history", "oral_history",
    "folklore", "proverb", "dictionary", "language", "corpus", "archive",
    "audio", "speech", "transcript", "recording", "dataset", "literature",
    "story", "stories", "book", "books", "sermon", "download", "zenodo",
    "huggingface", "commonvoice", "maseno", "africa", "african",
)
MAX_DISCOVERY_HOSTS = 40
MAX_PAGES_PER_HOST = 30


class WebCrawler(BaseCrawler):
    def crawl_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        base_host = (urlparse(base_url).hostname or "").lower()
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if not isinstance(href, str):
                continue
            absolute = urljoin(base_url, href)
            if not is_safe_http_url(absolute):
                continue
            target_host = (urlparse(absolute).hostname or "").lower()
            label = anchor.get_text(" ", strip=True).lower()
            searchable = f"{label} {absolute.lower()}"
            if target_host == base_host or any(term in searchable for term in RELEVANT_LINK_TERMS):
                links.append(canonicalize_url(absolute))
        return list(dict.fromkeys(links))[:200]

    async def crawl(self, seed_urls: list[str], max_pages: int = 500) -> list[dict]:
        safe_seeds = [canonicalize_url(url) for url in seed_urls if is_safe_http_url(url)]
        if not safe_seeds:
            logger.warning("crawler.no_safe_seeds")
            return []

        visited: set[str] = set()
        queued: set[str] = set(safe_seeds)
        queue: list[str] = list(safe_seeds)
        seed_hosts = {(urlparse(url).hostname or "").lower() for url in safe_seeds}
        discovered_hosts = set(seed_hosts)
        pages_by_host: dict[str, int] = {}
        results: list[dict] = []
        page_budget = max(1, min(max_pages, 1000))

        while queue and len(visited) < page_budget:
            url = queue.pop(0)
            if url in visited:
                continue
            host = (urlparse(url).hostname or "").lower()
            if not host or pages_by_host.get(host, 0) >= MAX_PAGES_PER_HOST:
                continue

            visited.add(url)
            pages_by_host[host] = pages_by_host.get(host, 0) + 1
            fetched = await self.fetch(url)
            if not fetched:
                continue

            html, final_url = fetched
            final_url = canonicalize_url(final_url)
            current_host = (urlparse(final_url).hostname or "").lower()
            if not current_host:
                continue

            # Notice-and-takedown ingestion: publicly accessible Gĩkũyũ material
            # is captured even if a page has no machine-readable licence. Unknown
            # rights never imply permission for AI training or commercial reuse.
            licence = self.detect_open_license(html, final_url)
            page = self.extract(html, final_url, licence or "UNKNOWN — licence not stated")
            if page and page.language == "ki" and page.confidence >= settings.LANGUAGE_DETECTION_THRESHOLD:
                # Discover every relevant Gĩkũyũ page, but only persist the
                # page body when an explicit reusable licence was identified.
                # Otherwise retain a source reference and descriptive metadata only.
                results.append({
                    "url": page.url,
                    "title": page.title,
                    "text": page.text if licence else None,
                    "language": page.language,
                    "confidence": page.confidence,
                    "license": page.license,
                    "license_url": page.license_url,
                    "permits_research": page.permits_research,
                    "permits_ai_training": page.permits_ai_training,
                    "permits_commercial_use": page.permits_commercial_use,
                    "rights_state": "identified_open_licence" if licence else "unknown_pending_rights_review",
                    "collection_mode": "full_text" if licence else "metadata_and_source_link_only",
                    "status": "approved" if licence else "pending",
                })
                logger.info("crawler.candidate_found", url=page.url, license=page.license)

            for link in self.crawl_links(html, final_url):
                if link in visited or link in queued:
                    continue
                target_host = (urlparse(link).hostname or "").lower()
                if not target_host or pages_by_host.get(target_host, 0) >= MAX_PAGES_PER_HOST:
                    continue
                if target_host != current_host and target_host not in discovered_hosts:
                    if len(discovered_hosts) >= MAX_DISCOVERY_HOSTS:
                        continue
                    discovered_hosts.add(target_host)
                if len(queue) < page_budget * 3:
                    queue.append(link)
                    queued.add(link)

        logger.info("crawler.crawl_complete", visited=len(visited), hosts=len(discovered_hosts), candidates=len(results))
        return results
