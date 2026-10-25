from app.crawlers.licensing import detect_open_licence, is_safe_http_url


def test_detects_explicit_cc0_license_link():
    html = """
    <html><head><title>Gĩkũyũ text</title>
    <link rel="license" href="https://creativecommons.org/publicdomain/zero/1.0/">
    </head><body><p>Gĩkũyũ text preserved for the community.</p></body></html>
    """
    licence = detect_open_licence(html, "https://example.org/text")
    assert licence is not None
    assert licence.name == "CC0-1.0"
    assert licence.permits_ai_training is True


def test_detects_explicit_cc_by_meta_license():
    html = """
    <html><head><meta name="license" content="CC-BY-4.0"></head>
    <body><p>Sample language text.</p></body></html>
    """
    licence = detect_open_licence(html, "https://example.org/text")
    assert licence is not None
    assert licence.name == "CC-BY-4.0"


def test_does_not_treat_mention_of_public_domain_as_a_license():
    html = """
    <html><head><title>Copyright history</title></head>
    <body><p>Some historical works have entered the public domain.</p>
    <p>This page is copyrighted and all rights are reserved.</p></body></html>
    """
    assert detect_open_licence(html, "https://example.org/text") is None


def test_does_not_accept_sharealike_or_noncommercial_licenses():
    html = """
    <html><head><link rel="license"
    href="https://creativecommons.org/licenses/by-sa/4.0/"></head>
    <body><p>Licensed under Creative Commons Attribution-ShareAlike.</p></body></html>
    """
    assert detect_open_licence(html, "https://example.org/text") is None


def test_accepts_explicit_public_domain_in_dedicated_license_section():
    html = """
    <html><body><article><p>Example text.</p></article>
    <section id="license"><p>Public domain</p></section></body></html>
    """
    licence = detect_open_licence(html, "https://example.org/text")
    assert licence is not None
    assert licence.name.startswith("Public Domain")


def test_rejects_non_http_and_obvious_private_urls():
    for url in ("file:///etc/passwd", "ftp://example.org/file", "http://localhost/admin",
                "http://127.0.0.1/", "http://169.254.169.254/latest/meta-data",
                "https://user:pass@example.org/"):
        assert is_safe_http_url(url) is False


def test_accepts_public_https_url():
    assert is_safe_http_url("https://example.org/open-data") is True
