import pytest

from app.crawlers.web import WebCrawler


GIKUYU_TEXT = (
    "Nĩ mũndũ wa Gĩkũyũ, na andũ a mũciĩ nĩ magĩtũũra hamwe. "
    "Ũhoro wa tene nĩ ũtũheaga ũmenyo na ũndũ wa gũtũũra wega. "
) * 3


@pytest.mark.asyncio
async def test_hunter_follows_relevant_cross_domain_links_and_keeps_unknown_rights(monkeypatch):
    crawler = WebCrawler()
    pages = {
        "https://seed.example/start": (
            "<html><head><title>Seed</title></head><body>"
            f"<p>{GIKUYU_TEXT}</p>"
            '<a href="https://other.example/gikuyu-oral-history">Gĩkũyũ oral history</a>'
            "</body></html>"
        ),
        "https://other.example/gikuyu-oral-history": (
            f"<html><head><title>Gĩkũyũ oral history</title></head><body><p>{GIKUYU_TEXT}</p></body></html>"
        ),
    }

    async def fake_fetch(url):
        return (pages[url], url) if url in pages else None

    monkeypatch.setattr(crawler, "fetch", fake_fetch)
    monkeypatch.setattr("app.crawlers.base.language_detector.detect", lambda text: ("ki", 0.95))

    results = await crawler.crawl(["https://seed.example/start"], max_pages=10)

    assert {item["url"] for item in results} == set(pages)
    assert all(item["language"] == "ki" for item in results)
    assert all(item["license"] == "UNKNOWN — licence not stated" for item in results)
    assert all(item["permits_research"] is False for item in results)
    assert all(item["permits_ai_training"] is False for item in results)
    assert all(item["permits_commercial_use"] is False for item in results)
    assert all(item["rights_state"] == "unknown_pending_rights_request" for item in results)


@pytest.mark.asyncio
async def test_hunter_does_not_follow_unrelated_external_links(monkeypatch):
    crawler = WebCrawler()
    html = (
        f"<html><head><title>Gĩkũyũ</title></head><body><p>{GIKUYU_TEXT}</p>"
        '<a href="https://other.example/weather">Weather report</a></body></html>'
    )

    async def fake_fetch(url):
        return (html, url)

    monkeypatch.setattr(crawler, "fetch", fake_fetch)
    monkeypatch.setattr("app.crawlers.base.language_detector.detect", lambda text: ("ki", 0.95))

    results = await crawler.crawl(["https://seed.example/start"], max_pages=10)

    assert len(results) == 1
    assert results[0]["url"] == "https://seed.example/start"
