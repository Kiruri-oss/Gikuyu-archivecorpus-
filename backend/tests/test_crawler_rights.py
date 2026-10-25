import pytest

from app.crawlers.base import BaseCrawler


def test_detects_explicit_cc0_license() -> None:
    html = '<html><head><link rel="license" href="https://creativecommons.org/publicdomain/zero/1.0/"></head><body>Gĩkũyũ text</body></html>'
    assert BaseCrawler.detect_open_license(html, "https://example.org/text") == "CC0"


def test_detects_explicit_cc_by_license() -> None:
    html = '<html><body><a rel="license" href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></body></html>'
    assert BaseCrawler.detect_open_license(html, "https://example.org/text") == "CC-BY"


def test_does_not_treat_public_access_as_a_license() -> None:
    html = "<html><head><title>Public Gĩkũyũ stories</title></head><body>Text is freely readable.</body></html>"
    assert BaseCrawler.detect_open_license(html, "https://example.org/text") is None


def test_rejects_private_and_non_http_targets() -> None:
    assert not BaseCrawler._is_public_http_url("http://127.0.0.1/admin")
    assert not BaseCrawler._is_public_http_url("http://localhost/private")
    assert not BaseCrawler._is_public_http_url("file:///etc/passwd")
    assert BaseCrawler._is_public_http_url("https://example.org/public")


@pytest.mark.asyncio
async def test_hunter_rejects_public_hostname_that_resolves_to_private_ip(monkeypatch):
    import socket
    from app.crawlers.base import BaseCrawler

    class PrivateDnsLoop:
        async def getaddrinfo(self, host, port, type):
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port))]

    monkeypatch.setattr("app.crawlers.base.asyncio.get_running_loop", lambda: PrivateDnsLoop())
    crawler = BaseCrawler()
    assert await crawler.can_fetch("https://public-looking.example/resource") is False
