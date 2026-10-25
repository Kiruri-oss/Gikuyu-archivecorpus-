import asyncio
import time
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
    license: str
    license_url: str | None = None
    permits_research: bool = True
    permits_ai_training: bool = True
    permits_commercial_use: bool = True


class BaseCrawler:
    """Rights-aware public web hunter with mandatory robots and host-delay compliance."""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
        }
        self.semaphore = asyncio.Semaphore(max(1, min(settings.CRAWLER_MAX_CONCURRENCY, 5)))
        self._robots: dict[str, RobotFileParser | None] = {}
        self._robots_lock = asyncio.Lock()
        self._host_last_request: dict[str, float] = {}
        self._host_delay_locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def _is_public_http_url(url: str) -> bool:
        return is_safe_http_url(url)

    async def _respect_host_delay(self, url: str) -> None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        lock = self._host_delay_locks.setdefault(origin, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            previous = self._host_last_request.get(origin)
            minimum_delay = max(0.0, float(settings.CRAWLER_MIN_HOST_DELAY_SECONDS))
            if previous is not None:
                wait = minimum_delay - (now - previous)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._host_last_request[origin] = time.monotonic()

    async def can_fetch(self, url: str) -> bool:
        if not is_safe_http_url(url):
            logger.warning("crawler.url_rejected", url=url, reason="unsafe_url")
            return False

        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with self._robots_lock:
            cached = origin in self._robots
            parser = self._robots.get(origin)
        if not cached:
            robots_url = f"{origin}/robots.txt"
            candidate = RobotFileParser()
            candidate.set_url(robots_url)
            try:
                async with httpx.AsyncClient(timeout=8, follow_redirects=False, headers=self.headers) as client:
                    response = await client.get(robots_url)
                if response.status_code == 404:
                    candidate.parse([])
                    parser = candidate
                elif response.status_code == 200:
                    candidate.parse(response.text.splitlines())
                    parser = candidate
                else:
                    parser = None
                    logger.warning("crawler.robots_unavailable", origin=origin, status=response.status_code)
            except httpx.HTTPError as exc:
                parser = None
                logger.warning("crawler.robots_fetch_failed", origin=origin, error=str(exc))
            async with self._robots_lock:
                self._robots[origin] = parser

        allowed = parser is not None and parser.can_fetch(settings.CRAWLER_USER_AGENT, url)
        if not allowed:
            logger.info("crawler.robots_disallowed_or_unknown", url=url)
        return allowed

    @classmethod
    def detect_open_license(cls, html: str, base_url: str) -> str | None:
        licence = detect_open_licence(html, base_url)
        return licence.name if licence else None

    async def fetch(self, url: str) -> tuple[str, str] | None:
        current_url = canonicalize_url(url) if is_safe_http_url(url) else url
        if not is_safe_http_url(current_url):
            logger.warning("crawler.url_rejected", url=url, reason="unsafe_url")
            return None

        async with self.semaphore:
            original_host = urlparse(current_url).hostname
            for _ in range(MAX_REDIRECTS + 1):
                if not is_safe_http_url(current_url) or not await self.can_fetch(current_url):
                    return None
                await self._respect_host_delay(current_url)
                try:
                    async with httpx.AsyncClient(timeout=20, follow_redirects=False, headers=self.headers) as client:
                        async with client.stream("GET", current_url) as response:
                            if response.status_code in {301, 302, 303, 307, 308}:
                                location = response.headers.get("location")
                                if not location:
                                    return None
                                target = canonicalize_url(urljoin(current_url, location))
                                if urlparse(target).hostname != original_host:
                                    logger.warning("crawler.cross_host_redirect_blocked", source=current_url, target=target)
                                    return None
                                current_url = target
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
                            html = b"".join(chunks).decode(encoding, errors="replace")
                            return html, current_url
                except (httpx.HTTPError, UnicodeError, LookupError, ValueError) as exc:
                    logger.warning("crawler.fetch_failed", url=current_url, error=str(exc))
                    return None
            logger.warning("crawler.redirect_limit", url=url)
            return None

    def extract(self, html: str, base_url: str, license_name: str) -> CrawlResult | None:
        soup = BeautifulSoup(html, "lxml")
        licence = detect_open_licence(html, base_url)
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title = (soup.title.string or "").strip() if soup.title else ""
        body = soup.get_text(separator=" ", strip=True)
        if len(body) < 100:
            return None

        language, score = language_detector.detect(body)
        links = [
            canonicalize_url(urljoin(base_url, str(anchor["href"])))
            for anchor in soup.find_all("a", href=True)
            if is_safe_http_url(urljoin(base_url, str(anchor["href"])))
        ]
        return CrawlResult(
            url=canonicalize_url(base_url),
            title=title[:500] or base_url,
            text=body[:50000],
            language=language,
            confidence=score,
            links=list(dict.fromkeys(links))[:100],
            license=licence.name if licence else license_name,
            license_url=licence.url or None if licence else None,
            permits_research=licence.permits_research if licence else True,
            permits_ai_training=licence.permits_ai_training if licence else True,
            permits_commercial_use=licence.permits_commercial_use if licence else True,
        )
