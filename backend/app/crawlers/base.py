import asyncio
import html as html_lib
import io
import socket
import time
import zipfile
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from ipaddress import ip_address

import httpx
import trafilatura
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.logging import get_logger
from app.crawlers.licensing import canonicalize_url, detect_open_licence, is_safe_http_url
from app.services.language_detector import language_detector

logger = get_logger(__name__)
settings = get_settings()
MAX_PAGE_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 500
MAX_EPUB_ENTRIES = 300
MAX_EPUB_TEXT_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_TEXT_CHARS = 250000
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
    permits_research: bool = False
    permits_ai_training: bool = False
    permits_commercial_use: bool = False


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

    async def _has_public_dns_target(self, url: str) -> bool:
        """Reject public-looking hostnames that resolve to private or special IPs."""
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False
        try:
            return ip_address(host).is_global
        except ValueError:
            pass
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            answers = await asyncio.get_running_loop().getaddrinfo(
                host, port, type=socket.SOCK_STREAM
            )
        except (OSError, asyncio.TimeoutError, socket.gaierror) as exc:
            logger.warning("crawler.dns_resolution_failed", host=host, error=str(exc))
            return False
        addresses = {answer[4][0].split("%", 1)[0] for answer in answers}
        if not addresses:
            return False
        for address in addresses:
            try:
                if not ip_address(address).is_global:
                    logger.warning("crawler.private_dns_target_blocked", host=host, address=address)
                    return False
            except ValueError:
                return False
        return True

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
        if not await self._has_public_dns_target(url):
            logger.warning("crawler.url_rejected", url=url, reason="non_public_dns_target")
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

    @staticmethod
    def _pdf_to_html(payload: bytes, source_url: str) -> str | None:
        """Extract bounded text from public PDFs so books and scanned reports enter discovery."""
        try:
            reader = PdfReader(io.BytesIO(payload), strict=False)
            if reader.is_encrypted:
                try:
                    if not reader.decrypt(""):
                        logger.info("crawler.encrypted_pdf_skipped", url=source_url)
                        return None
                except Exception:
                    logger.info("crawler.encrypted_pdf_skipped", url=source_url)
                    return None

            chunks: list[str] = []
            for page in reader.pages[:MAX_PDF_PAGES]:
                try:
                    extracted = page.extract_text() or ""
                except Exception as exc:
                    logger.warning("crawler.pdf_page_extract_failed", url=source_url, error=str(exc))
                    continue
                if extracted.strip():
                    chunks.append(extracted.strip())
            text = "\n\n".join(chunks)[:MAX_EXTRACTED_TEXT_CHARS]
            if not text.strip():
                logger.info("crawler.pdf_has_no_extractable_text", url=source_url)
                return None

            metadata = reader.metadata
            title = str(getattr(metadata, "title", "") or "").strip()
            if not title:
                title = urlparse(source_url).path.rsplit("/", 1)[-1] or "PDF document"
            return (
                "<html><head><title>"
                + html_lib.escape(title)
                + "</title></head><body><pre>"
                + html_lib.escape(text)
                + "</pre></body></html>"
            )
        except Exception as exc:
            logger.warning("crawler.pdf_parse_failed", url=source_url, error=str(exc))
            return None

    @staticmethod
    def _epub_to_html(payload: bytes, source_url: str) -> str | None:
        """Read bounded XHTML from an EPUB without extracting archive files to disk."""
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as book:
                entries = book.infolist()
                if len(entries) > MAX_EPUB_ENTRIES:
                    logger.info("crawler.epub_entry_limit_exceeded", url=source_url, entries=len(entries))
                    entries = entries[:MAX_EPUB_ENTRIES]

                extracted_bytes = 0
                chapters: list[str] = []
                title = ""
                for entry in entries:
                    path = entry.filename.lower()
                    if not path.endswith((".xhtml", ".html", ".htm")):
                        continue
                    if entry.flag_bits & 0x1 or entry.file_size > MAX_PAGE_BYTES:
                        continue
                    if entry.compress_size > 0 and entry.file_size / entry.compress_size > 200:
                        logger.info("crawler.epub_compression_ratio_rejected", url=source_url, member=entry.filename)
                        continue
                    if extracted_bytes + entry.file_size > MAX_EPUB_TEXT_BYTES:
                        break

                    raw = book.read(entry)
                    extracted_bytes += len(raw)
                    soup = BeautifulSoup(raw, "lxml")
                    if not title and soup.title:
                        title = soup.title.get_text(" ", strip=True)
                    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                        tag.decompose()
                    chapter = soup.get_text(separator=" ", strip=True)
                    if chapter:
                        chapters.append(chapter)

                text = "\\n\\n".join(chapters)[:MAX_EXTRACTED_TEXT_CHARS]
                if not text.strip():
                    logger.info("crawler.epub_has_no_extractable_text", url=source_url)
                    return None
                if not title:
                    title = urlparse(source_url).path.rsplit("/", 1)[-1] or "EPUB book"
                return (
                    "<html><head><title>"
                    + html_lib.escape(title)
                    + "</title></head><body><pre>"
                    + html_lib.escape(text)
                    + "</pre></body></html>"
                )
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
            logger.warning("crawler.epub_parse_failed", url=source_url, error=str(exc))
            return None

    async def fetch(self, url: str) -> tuple[str, str] | None:
        current_url = canonicalize_url(url) if is_safe_http_url(url) else url
        if not is_safe_http_url(current_url):
            logger.warning("crawler.url_rejected", url=url, reason="unsafe_url")
            return None

        async with self.semaphore:
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
                                # Revalidate the new host, public DNS target and its robots.txt
                                # on the next loop. Archive/CDN redirects are common for books.
                                current_url = target
                                continue
                            if response.status_code >= 400:
                                logger.warning("crawler.http_error", url=current_url, status=response.status_code)
                                return None
                            content_type = response.headers.get("content-type", "").lower()
                            path = urlparse(current_url).path.lower()
                            is_pdf = "application/pdf" in content_type or path.endswith(".pdf")
                            is_epub = "application/epub+zip" in content_type or path.endswith(".epub")
                            if not (is_pdf or is_epub) and content_type and not any(
                                kind in content_type
                                for kind in ("text/html", "application/xhtml+xml")
                            ):
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
                            payload = b"".join(chunks)
                            if is_pdf:
                                document_html = await asyncio.to_thread(
                                    self._pdf_to_html, payload, current_url
                                )
                                if document_html is None:
                                    return None
                                return document_html, current_url
                            if is_epub:
                                document_html = await asyncio.to_thread(
                                    self._epub_to_html, payload, current_url
                                )
                                if document_html is None:
                                    return None
                                return document_html, current_url
                            encoding = response.encoding or "utf-8"
                            html = payload.decode(encoding, errors="replace")
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
        body = ""
        try:
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_links=False,
                favor_precision=False,
            )
            if extracted:
                body = extracted.strip()
        except Exception as exc:
            logger.debug("crawler.main_text_extraction_fallback", url=base_url, error=str(exc))
        if len(body) < 100:
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
            permits_research=licence.permits_research if licence else False,
            permits_ai_training=licence.permits_ai_training if licence else False,
            permits_commercial_use=licence.permits_commercial_use if licence else False,
        )
