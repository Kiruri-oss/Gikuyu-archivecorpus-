from types import SimpleNamespace

import pytest

from app.crawlers.web import WebCrawler


@pytest.mark.asyncio
async def test_hunter_follows_cross_domain_links_within_budget(monkeypatch):
    crawler = WebCrawler()
    fetched_urls = []

    async def fake_fetch(url):
        fetched_urls.append(url)
        if url == "https://seed.example/start":
            return (
                '<html><head><title>Seed catalogue</title></head>'
                '<body><a href="https://second.example/gikuyu">Gĩkũyũ collection</a></body></html>',
                url,
            )
        return (
            '<html><head><title>Gĩkũyũ collection</title></head><body>Reference listing</body></html>',
            url,
        )

    monkeypatch.setattr(crawler, "fetch", fake_fetch)
    monkeypatch.setattr(crawler, "detect_open_license", lambda html, url: None)

    results = await crawler.crawl(
        ["https://seed.example/start"],
        max_pages=10,
        max_domains=2,
        max_pages_per_domain=2,
    )

    assert fetched_urls == [
        "https://seed.example/start",
        "https://second.example/gikuyu",
    ]
    assert [item["url"] for item in results] == fetched_urls
    assert all(item["archive_content"] is False for item in results)
    assert all(item["license"] == "UNVERIFIED" for item in results)


@pytest.mark.asyncio
async def test_hunter_archives_only_confident_gikuyu_text_with_open_licence(monkeypatch):
    crawler = WebCrawler()
    html = '<html><head><title>Gĩkũyũ proverb</title></head><body>proverb</body></html>'

    async def fake_fetch(url):
        return html, url

    monkeypatch.setattr(crawler, "fetch", fake_fetch)
    monkeypatch.setattr(crawler, "detect_open_license", lambda _html, _url: "CC-BY")
    monkeypatch.setattr(
        crawler,
        "extract",
        lambda _html, url, _license: SimpleNamespace(
            url=url,
            title="Gĩkũyũ proverb",
            text="Mũciĩ wa mũndũ.",
            language="ki",
            confidence=0.99,
            license="CC-BY",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            permits_research=True,
            permits_ai_training=True,
            permits_commercial_use=True,
        ),
    )

    results = await crawler.crawl(
        ["https://archive.example/gikuyu"],
        max_pages=1,
        max_domains=1,
        max_pages_per_domain=1,
    )

    assert len(results) == 1
    assert results[0]["archive_content"] is True
    assert results[0]["language"] == "ki"
    assert results[0]["text"] == "Mũciĩ wa mũndũ."
    assert results[0]["license"] == "CC-BY"
