import pytest

from app.crawlers.web import WebCrawler


@pytest.mark.asyncio
async def test_crawler_discovers_through_unlicensed_index_and_archives_gikuyu_candidates(monkeypatch):
    pages = {
        "https://example.org/": """
            <html><head><title>Index</title></head><body>
            <p>Gĩkũyũ community language index with enough explanatory text to pass
            the crawler's minimum page length requirement and preserve useful links.</p>
            <a href="/licensed">Licensed story</a>
            <a href="https://other.example/unrelated">External page</a>
            </body></html>
        """,
        "https://example.org/licensed": """
            <html><head><title>Gĩkũyũ proverb collection</title>
            <link rel="license" href="https://creativecommons.org/licenses/by/4.0/">
            </head><body><p>Gĩkũyũ proverb and oral tradition text. This page is explicitly
            licensed for reuse under the Creative Commons Attribution 4.0 International
            licence. Enough content is included for the minimum length requirement.</p></body></html>
        """,
    }

    async def fake_fetch(url: str):
        return (pages[url], url) if url in pages else None

    monkeypatch.setattr("app.services.language_detector.language_detector.detect", lambda _text: ("ki", 0.95))
    crawler = WebCrawler()
    monkeypatch.setattr(crawler, "fetch", fake_fetch)

    results = await crawler.crawl(["https://example.org/"], max_pages=10)

    assert len(results) == 2
    by_url = {item["url"]: item for item in results}
    assert by_url["https://example.org/"]["license"] == "UNKNOWN — licence not stated"
    assert by_url["https://example.org/"]["permits_ai_training"] is False
    assert by_url["https://example.org/licensed"]["license"] == "CC-BY"
    assert by_url["https://example.org/licensed"]["permits_ai_training"] is True


@pytest.mark.asyncio
async def test_crawler_archives_cc_by_sa_candidate_but_does_not_grant_reuse(monkeypatch):
    html = """
        <html><head><title>Gĩkũyũ text</title>
        <link rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">
        </head><body><p>Gĩkũyũ content under CC BY-SA 4.0. This content is long enough
        for the minimum crawler page length check but must not be accepted for automatic
        AI-training or commercial reuse without applying its terms.</p></body></html>
    """

    async def fake_fetch(url: str):
        return html, url

    monkeypatch.setattr("app.services.language_detector.language_detector.detect", lambda _text: ("ki", 0.95))
    crawler = WebCrawler()
    monkeypatch.setattr(crawler, "fetch", fake_fetch)
    results = await crawler.crawl(["https://example.org/"], max_pages=1)

    assert len(results) == 1
    assert results[0]["license"] == "UNKNOWN — licence not stated"
    assert results[0]["permits_research"] is False
    assert results[0]["permits_ai_training"] is False
    assert results[0]["permits_commercial_use"] is False


@pytest.mark.asyncio
async def test_crawler_applies_a_minimum_delay_between_requests_to_the_same_host(monkeypatch):
    import time
    from app.crawlers.base import BaseCrawler

    monkeypatch.setattr("app.crawlers.base.settings.CRAWLER_MIN_HOST_DELAY_SECONDS", 0.02)
    crawler = BaseCrawler()
    await crawler._respect_host_delay("https://example.org/first")
    started = time.monotonic()
    await crawler._respect_host_delay("https://example.org/second")
    assert time.monotonic() - started >= 0.015


@pytest.mark.asyncio
async def test_crawler_does_not_apply_host_delay_across_different_origins(monkeypatch):
    import time
    from app.crawlers.base import BaseCrawler

    monkeypatch.setattr("app.crawlers.base.settings.CRAWLER_MIN_HOST_DELAY_SECONDS", 0.05)
    crawler = BaseCrawler()
    await crawler._respect_host_delay("https://one.example/first")
    started = time.monotonic()
    await crawler._respect_host_delay("https://two.example/second")
    assert time.monotonic() - started < 0.04


def test_pdf_text_extraction_produces_crawlable_gikuyu_document(monkeypatch):
    from types import SimpleNamespace

    from bs4 import BeautifulSoup

    from app.crawlers.base import BaseCrawler

    class FakePage:
        def extract_text(self):
            return "Gĩkũyũ: Nĩ mũndũ ũcio. Mũciĩ na andũ."

    class FakeReader:
        def __init__(self, _stream, strict=False):
            self.is_encrypted = False
            self.pages = [FakePage()]
            self.metadata = SimpleNamespace(title="Gĩkũyũ oral tradition")

    monkeypatch.setattr("app.crawlers.base.PdfReader", FakeReader)
    document = BaseCrawler._pdf_to_html(b"%PDF test fixture", "https://example.org/story.pdf")

    assert document is not None
    parsed = BeautifulSoup(document, "lxml")
    assert parsed.title is not None
    assert parsed.title.get_text() == "Gĩkũyũ oral tradition"
    assert "Nĩ mũndũ ũcio" in parsed.get_text()
    assert "mũciĩ" in parsed.get_text().lower()


def test_pdf_extraction_skips_encrypted_files_without_an_empty_password(monkeypatch):
    from app.crawlers.base import BaseCrawler

    class FakeReader:
        def __init__(self, _stream, strict=False):
            self.is_encrypted = True
            self.pages = []
            self.metadata = None

        def decrypt(self, _password):
            return 0

    monkeypatch.setattr("app.crawlers.base.PdfReader", FakeReader)
    assert BaseCrawler._pdf_to_html(b"%PDF encrypted fixture", "https://example.org/locked.pdf") is None
