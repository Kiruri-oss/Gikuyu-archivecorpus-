from collections import deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler
from app.crawlers.licensing import canonicalize_url, is_safe_http_url
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_SKIP_PATH_PARTS = (
    "/login", "/logout", "/signin", "/signup", "/register",
    "/cart", "/checkout", "/account", "/wp-admin",
)
_SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".css", ".js",
    ".ico", ".woff", ".woff2", ".ttf", ".zip", ".gz", ".mp4", ".mp3",
    ".wav", ".avi", ".mov", ".exe",
)


class WebCrawler(BaseCrawler):
    """Bounded multi-domain Gĩkũyũ source hunter.

    It indexes leads across the public web, respecting robots.txt and strict
    page/domain budgets. Full text is extracted only when an explicit supported
    open licence is present and the language detector identifies Gĩkũyũ.
    Other pages remain source leads with URL/title/rights state, not copied text.
    """

    def crawl_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if not isinstance(href, str):
                continue
            absolute = urljoin(base_url, href)
            if not is_safe_http_url(absolute):
                continue
            path = urlparse(absolute).path.lower()
            if any(part in path for part in _SKIP_PATH_PARTS) or path.endswith(_SKIP_EXTENSIONS):
                continue
            links.append(canonicalize_url(absolute))
        return list(dict.fromkeys(links))[:250]

    @staticmethod
    def _page_title(html: str, url: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return (soup.title.get_text(" ", strip=True) if soup.title else "")[:500] or url

    async def crawl(
        self,
        seed_urls: list[str],
        max_pages: int = 250,
        max_domains: int = 75,
        max_pages_per_domain: int = 12,
    ) -> list[dict]:
        safe_seeds = list(dict.fromkeys(
            canonicalize_url(url) for url in seed_urls if is_safe_http_url(url)
        ))
        page_budget = max(1, min(max_pages, 5000))
        domain_budget = max(1, min(max_domains, 500))
        per_domain_budget = max(1, min(max_pages_per_domain, 100))

        queue = deque(safe_seeds)
        queued = set(safe_seeds)
        visited: set[str] = set()
        domains: set[str] = set()
        domain_visits: dict[str, int] = {}
        results: list[dict] = []

        while queue and len(visited) < page_budget:
            url = queue.popleft()
            if url in visited:
                continue
            host = (urlparse(url).hostname or "").lower()
            if not host or (host not in domains and len(domains) >= domain_budget):
                continue
            if domain_visits.get(host, 0) >= per_domain_budget:
                continue

            visited.add(url)
            domains.add(host)
            domain_visits[host] = domain_visits.get(host, 0) + 1
            fetched = await self.fetch(url)
            if not fetched:
                continue

            html, final_url = fetched
            final_url = canonicalize_url(final_url)
            final_host = (urlparse(final_url).hostname or "").lower()
            if not final_host:
                continue
            domains.add(final_host)

            links = self.crawl_links(html, final_url)
            licence = self.detect_open_license(html, final_url)
            title = self._page_title(html, final_url)
            candidate = {
                "url": final_url,
                "title": title,
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "license": licence or "UNVERIFIED",
                "license_url": None,
                "permits_research": False,
                "permits_ai_training": False,
                "permits_commercial_use": False,
                "archive_content": False,
                "status": "pending",
            }

            if licence:
                page = self.extract(html, final_url, licence)
                if page:
                    candidate.update({
                        "title": page.title,
                        "language": page.language,
                        "confidence": page.confidence,
                        "license": page.license,
                        "license_url": page.license_url,
                        "permits_research": page.permits_research,
                        "permits_ai_training": page.permits_ai_training,
                        "permits_commercial_use": page.permits_commercial_use,
                    })
                    if page.language == "ki" and page.confidence >= settings.LANGUAGE_DETECTION_THRESHOLD:
                        candidate["text"] = page.text
                        candidate["archive_content"] = True
                        logger.info("crawler.gikuyu_content_candidate", url=page.url, license=page.license)
                    else:
                        logger.info("crawler.source_lead_found", url=page.url, reason="not_confidently_gikuyu")
            else:
                logger.info("crawler.source_lead_found", url=final_url, reason="rights_not_detected")

            # Every reachable lead is retained as source metadata; only explicitly
            # licensed Gĩkũyũ text is copied into the text corpus.
            results.append(candidate)

            # Follow cross-domain references to expand discovery beyond the seeds.
            for link in links:
                if link in visited or link in queued:
                    continue
                link_host = (urlparse(link).hostname or "").lower()
                if not link_host:
                    continue
                if link_host not in domains and len(domains) >= domain_budget:
                    continue
                if domain_visits.get(link_host, 0) >= per_domain_budget:
                    continue
                if len(queue) < page_budget * 3:
                    queue.append(link)
                    queued.add(link)

        logger.info(
            "crawler.crawl_complete",
            visited=len(visited),
            domains=len(domains),
            source_leads=len(results),
            licensed_gikuyu_text=sum(1 for item in results if item["archive_content"]),
            page_budget=page_budget,
            domain_budget=domain_budget,
        )
        return results
