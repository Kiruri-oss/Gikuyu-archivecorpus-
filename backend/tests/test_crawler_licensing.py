from app.crawlers.licensing import canonicalize_url, detect_open_licence, is_safe_http_url


def test_accepts_only_exact_creative_commons_hosts_and_paths():
    accepted = '<html><head><link rel="license" href="https://creativecommons.org/licenses/by/4.0/"></head><body>Text</body></html>'
    rejected = '<html><head><link rel="license" href="https://attacker.example/creativecommons.org/licenses/by/4.0/"></head><body>Text</body></html>'
    assert detect_open_licence(accepted, "https://example.org/text").name == "CC-BY"
    assert detect_open_licence(rejected, "https://example.org/text") is None


def test_rejects_sharealike_and_noncommercial_licences():
    for href in (
        "https://creativecommons.org/licenses/by-sa/4.0/",
        "https://creativecommons.org/licenses/by-nc/4.0/",
    ):
        html = f'<html><head><link rel="license" href="{href}"></head><body>Text</body></html>'
        assert detect_open_licence(html, "https://example.org/text") is None


def test_public_domain_requires_a_dedicated_rights_section():
    vague = "<html><body><p>Some older books are now in the public domain.</p></body></html>"
    explicit = '<html><body><section id="license">Public domain</section></body></html>'
    assert detect_open_licence(vague, "https://example.org/text") is None
    assert detect_open_licence(explicit, "https://example.org/text").name == "PUBLIC-DOMAIN"


def test_canonicalise_source_urls_and_reject_private_targets():
    assert canonicalize_url("HTTPS://Example.ORG:443/page?q=1#section") == "https://example.org/page?q=1"
    assert not is_safe_http_url("http://127.0.0.1/admin")
    assert not is_safe_http_url("http://169.254.169.254/latest/meta-data")
    assert not is_safe_http_url("https://example.org:8443/")
    assert is_safe_http_url("https://example.org/public")
