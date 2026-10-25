import pytest

from app.crawlers.web import WebCrawler


@pytest.mark.asyncio
async def test_crawler_discovers_through_unlicensed_index_but_archives_only_licensed(monkeypatch):
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

    assert len(results) == 1
    assert results[0]["url"] == "https://example.org/licensed"
    assert results[0]["license"] == "CC-BY"
    assert results[0]["permits_ai_training"] is True


@pytest.mark.asyncio
async def test_crawler_does_not_archive_cc_by_sa(monkeypatch):
    html = """
        <html><head><title>Gĩkũyũ text</title>
        <link rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">
        </head><body><p>Gĩkũyũ content under CC BY-SA 4.0. This content is long enough
        for the minimum crawler page length check but must not be accepted.</p></body></html>
    """

    async def fake_fetch(url: str):
        return html, url

    monkeypatch.setattr("app.services.language_detector.language_detector.detect", lambda _text: ("ki", 0.95))
    crawler = WebCrawler()
    monkeypatch.setattr(crawler, "fetch", fake_fetch)
    results = await crawler.crawl(["https://example.org/"], max_pages=1)
    assert results == []
