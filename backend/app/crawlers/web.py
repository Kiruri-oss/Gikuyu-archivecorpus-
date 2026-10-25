from collections import deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler
from app.crawlers.licensing import canonicalize_url, is_safe_http_url
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Avoid obvious crawler traps while retaining ordinary article, book and catalogue
# URLs. Query parameters are retained because many digital libraries use them.
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
    """Bounded multi-domain Gĩkũyũ web hunter.

    It follows external references rather than staying trapped on each seed host,
    but applies strict page/domain budgets, URL safety checks and robots.txt on
    every origin. Only pages with an explicitly detected supported open licence
    are extracted as corpus text; other pages can reveal further source leads.
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
            parsed = urlparse(absolute)
            path = parsed.path.lower()
            if any(part in path for part in _SKIP_PATH_PARTS):
                continue
            if path.endswith(_SKIP_EXTENSIONS):
                continue
            links.append(canonicalize_url(absolute))
        return list(dict.fromkeys(links))[:250]

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
            if not host:
                continue
            if host not in domains and len(domains) >= domain_budget:
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

            # Links are useful discovery leads even when a page has no explicit
            # open licence. Unlicensed page text is never copied into the corpus.
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
                logger.info("crawler.source_lead_found", url=final_url, reason="no_explicit_open_license")

            # Cross-domain traversal is what makes this a hunter rather than a
            # seed-site-only spider. Per-domain and global budgets prevent traps.
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
            candidates=len(results),
            page_budget=page_budget,
            domain_budget=domain_budget,
        )
        return results
