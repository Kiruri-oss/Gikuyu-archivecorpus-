import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

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


class BaseCrawler:
    def __init__(self) -> None:
        self.headers = {"User-Agent": settings.CRAWLER_USER_AGENT}
        self.semaphore = asyncio.Semaphore(settings.CRAWLER_MAX_CONCURRENCY)

    async def fetch(self, url: str) -> str | None:
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(
                    timeout=20, follow_redirects=True, headers=self.headers
                ) as client:
                    resp = await client.get(url)
                    if resp.status_code >= 400:
                        logger.warning("crawler.http_error", url=url, status=resp.status_code)
                        return None
                    return resp.text
            except httpx.HTTPError as exc:
                logger.warning("crawler.fetch_failed", url=url, error=str(exc))
                return None

    def extract(self, html: str, base_url: str) -> CrawlResult | None:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = (soup.title.string or "").strip() if soup.title else ""
        body = soup.get_text(separator=" ", strip=True)

        if len(body) < 200:
            return None

        lang, score = language_detector.detect(body)
        links = [
            a["href"] for a in soup.find_all("a", href=True)
            if a["href"].startswith("http")
        ]

        return CrawlResult(
            url=base_url,
            title=title,
            text=body[:50000],
            language=lang,
            confidence=score,
            links=links[:100],
        )