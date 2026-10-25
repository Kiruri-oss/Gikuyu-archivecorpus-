import asyncio
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.language_detector import language_detector

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class CrawlResult:
    url: str
    title: str
    text: str
    language: str
    confidence: float
    links: list[str]
    license: str


class BaseCrawler:
    """Rights-first public web hunter.

    A page is eligible for content extraction only when robots.txt permits access
    and an explicit supported open licence can be identified. Discovery metadata
    for a blocked/unlicensed page must not be mistaken for an archived copy.
    """

    OPEN_LICENSES = {
        "CC0": re.compile(r"(?:creativecommons\.org/publicdomain/zero|\bcc0\b|public domain dedication)", re.I),
        "CC-BY": re.compile(r"creativecommons\.org/licenses/by(?:/|\s|$)", re.I),
        "PUBLIC-DOMAIN": re.compile(r"(?:\bpublic domain\b|\bpublic-domain\b)", re.I),
        "KE-GOV-OPEN": re.compile(r"(?:kenya government open data|government of kenya open data licence|open data licence of the government of kenya)", re.I),
    }

    def __init__(self) -> None:
        self.headers = {"User-Agent": settings.CRAWLER_USER_AGENT}
        self.semaphore = asyncio.Semaphore(max(1, settings.CRAWLER_MAX_CONCURRENCY))
        self._robots: dict[str, RobotFileParser | None] = {}

    @staticmethod
    def _is_public_http_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                return False
            host = parsed.hostname.lower().rstrip(".")
            if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
                return False
            try:
                address = ipaddress.ip_address(host)
            except ValueError:
                address = None
            if address is not None and (not address.is_global):
                return False
            return True
        except (ValueError, TypeError):
            return False

    async def can_fetch(self, url: str) -> bool:
        if not self._is_public_http_url(url):
            logger.warning("crawler.url_rejected", url=url, reason="unsafe_url")
            return False
        if not settings.CRAWLER_RESPECT_ROBOTS:
            return True

        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            robots_url = f"{origin}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                async with httpx.AsyncClient(timeout=8, follow_redirects=False, headers=self.headers) as client:
                    response = await client.get(robots_url)
                if response.status_code == 404:
                    parser.parse([])
                    self._robots[origin] = parser
                elif response.status_code == 200:
                    parser.parse(response.text.splitlines())
                    self._robots[origin] = parser
                else:
                    # Fail closed on rate limits, server errors, and ambiguous robots responses.
                    self._robots[origin] = None
                    logger.warning("crawler.robots_unavailable", origin=origin, status=response.status_code)
            except httpx.HTTPError as exc:
                self._robots[origin] = None
                logger.warning("crawler.robots_fetch_failed", origin=origin, error=str(exc))

        parser = self._robots[origin]
        allowed = parser is not None and parser.can_fetch(settings.CRAWLER_USER_AGENT, url)
        if not allowed:
            logger.info("crawler.robots_disallowed", url=url)
        return allowed

    @classmethod
    def detect_open_license(cls, html: str, base_url: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")
        signals: list[str] = []
        for tag in soup.find_all(True):
            rel = tag.get("rel", [])
            rel_values = rel if isinstance(rel, list) else [rel]
            if any(str(value).lower() == "license" for value in rel_values):
                href = tag.get("href")
                if href:
                    signals.append(urljoin(base_url, str(href)))
            for attr in ("content", "href", "data-license", "property", "name"):
                value = tag.get(attr)
                if value and any(term in str(tag).lower() for term in ("license", "licence", "rights", "copyright")):
                    signals.append(str(value))
            if tag.name in {"a", "link", "meta"}:
                label = " ".join(str(tag.get(key, "")) for key in ("title", "aria-label", "rel", "property", "name", "content"))
                label += " " + tag.get_text(" ", strip=True)
                if re.search(r"licen[cs]e|public domain|open data|creativecommons|cc-by|cc0", label, re.I):
                    signals.append(label)

        # Only explicit, identifiable licence signals qualify; a page being public is not a licence.
        combined = " ".join(signals)
        for name, pattern in cls.OPEN_LICENSES.items():
            if pattern.search(combined):
                return name
        return None

    async def fetch(self, url: str) -> tuple[str, str] | None:
        if not await self.can_fetch(url):
            return None
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(
                    timeout=20, follow_redirects=False, headers=self.headers
                ) as client:
                    response = await client.get(url)
                    if response.status_code in {301, 302, 303, 307, 308}:
                        target = urljoin(url, response.headers.get("location", ""))
                        if not self._is_public_http_url(target) or not await self.can_fetch(target):
                            return None
                        response = await client.get(target)
                    if response.status_code >= 400:
                        logger.warning("crawler.http_error", url=url, status=response.status_code)
                        return None
                    final_url = str(response.url)
                    if not self._is_public_http_url(final_url):
                        return None
                    return response.text, final_url
            except httpx.HTTPError as exc:
                logger.warning("crawler.fetch_failed", url=url, error=str(exc))
                return None

    def extract(self, html: str, base_url: str, license_name: str) -> CrawlResult | None:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = (soup.title.string or "").strip() if soup.title else ""
        body = soup.get_text(separator=" ", strip=True)
        if len(body) < 200:
            return None

        language, score = language_detector.detect(body)
        links = [
            urljoin(base_url, str(anchor["href"]))
            for anchor in soup.find_all("a", href=True)
            if self._is_public_http_url(urljoin(base_url, str(anchor["href"])))
        ]
        return CrawlResult(
            url=base_url,
            title=title,
            text=body[:50000],
            language=language,
            confidence=score,
            links=list(dict.fromkeys(links))[:100],
            license=license_name,
        )
