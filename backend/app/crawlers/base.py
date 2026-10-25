import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger
from app.crawlers.licensing import canonicalize_url, detect_open_licence, is_safe_http_url
from app.services.language_detector import language_detector

logger = get_logger(__name__)
settings = get_settings()
MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 5


@dataclass
class CrawlResult:
    url: str
    title: str
    text: str
    language: str
    confidence: float
    links: list[str]
    license: str | None = None
    license_url: str | None = None
    permits_research: bool = False
    permits_ai_training: bool = False
    permits_commercial_use: bool = False


class BaseCrawler:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
        }
        self.semaphore = asyncio.Semaphore(max(1, min(settings.CRAWLER_MAX_CONCURRENCY, 5)))
        self._robots_cache: dict[str, RobotFileParser | None] = {}
        self._robots_lock = asyncio.Lock()

    async def _robots_for(self, url: str) -> RobotFileParser | None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with self._robots_lock:
            if origin in self._robots_cache:
                return self._robots_cache[origin]

        parser = RobotFileParser()
        parser.set_url(f"{origin}/robots.txt")
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=False, headers=self.headers) as client:
                response = await client.get(parser.url)
            if response.status_code == 404:
                parser.parse([])
            elif response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                logger.warning("crawler.robots_unavailable", origin=origin, status=response.status_code)
                return None
        except httpx.HTTPError as exc:
            logger.warning("crawler.robots_fetch_failed", origin=origin, error=str(exc))
            return None

        async with self._robots_lock:
            self._robots_cache[origin] = parser
        return parser

    async def _allowed_by_robots(self, url: str) -> bool:
        # This corpus hunter always honours robots.txt; configuration cannot disable it.
        parser = await self._robots_for(url)
        return parser is not None and parser.can_fetch(settings.CRAWLER_USER_AGENT, url)

    async def fetch(self, url: str) -> str | None:
        if not is_safe_http_url(url):
            logger.warning("crawler.unsafe_url_rejected", url=url)
            return None

        async with self.semaphore:
            current_url = url
            for _ in range(MAX_REDIRECTS + 1):
                if not is_safe_http_url(current_url) or not await self._allowed_by_robots(current_url):
                    logger.info("crawler.robots_or_safety_block", url=current_url)
                    return None
                try:
                    async with httpx.AsyncClient(
                        timeout=20, follow_redirects=False, headers=self.headers
                    ) as client:
                        async with client.stream("GET", current_url) as response:
                            if response.status_code in {301, 302, 303, 307, 308}:
                                location = response.headers.get("location")
                                if not location:
                                    return None
                                redirect_url = urljoin(current_url, location)
                                if urlparse(redirect_url).hostname != urlparse(current_url).hostname:
                                    logger.warning("crawler.cross_host_redirect_blocked", source=current_url, target=redirect_url)
                                    return None
                                current_url = redirect_url
                                continue
                            if response.status_code >= 400:
                                logger.warning("crawler.http_error", url=current_url, status=response.status_code)
                                return None
                            content_type = response.headers.get("content-type", "").lower()
                            if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml+xml")):
                                logger.info("crawler.non_html_skipped", url=current_url, content_type=content_type)
                                return None
                            length = response.headers.get("content-length")
                            if length and int(length) > MAX_PAGE_BYTES:
                                logger.warning("crawler.page_too_large", url=current_url, bytes=length)
                                return None
                            chunks: list[bytes] = []
                            total = 0
                            async for chunk in response.aiter_bytes():
                                total += len(chunk)
                                if total > MAX_PAGE_BYTES:
                                    logger.warning("crawler.page_too_large", url=current_url, bytes=total)
                                    return None
                                chunks.append(chunk)
                            encoding = response.encoding or "utf-8"
                            return b"".join(chunks).decode(encoding, errors="replace")
                except (httpx.HTTPError, UnicodeError, LookupError, ValueError) as exc:
                    logger.warning("crawler.fetch_failed", url=current_url, error=str(exc))
                    return None
            logger.warning("crawler.redirect_limit", url=url)
            return None

    def extract(self, html: str, base_url: str) -> CrawlResult | None:
        soup = BeautifulSoup(html, "lxml")
        licence = detect_open_licence(html, base_url)
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title = (soup.title.string or "").strip() if soup.title else ""
        body = soup.get_text(separator=" ", strip=True)
        if len(body) < 100:
            return None

        lang, score = language_detector.detect(body)
        links = [
            canonicalize_url(urljoin(base_url, anchor["href"]))
            for anchor in soup.find_all("a", href=True)
            if is_safe_http_url(urljoin(base_url, anchor["href"]))
        ]
        return CrawlResult(
            url=base_url,
            title=title[:500] or base_url,
            text=body[:50000],
            language=lang,
            confidence=score,
            links=list(dict.fromkeys(links))[:100],
            license=licence.name if licence else None,
            license_url=(licence.url or None) if licence else None,
            permits_research=licence.permits_research if licence else False,
            permits_ai_training=licence.permits_ai_training if licence else False,
            permits_commercial_use=licence.permits_commercial_use if licence else False,
        )
