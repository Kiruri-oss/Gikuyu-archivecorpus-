"""Conservative licence detection for the automatic corpus hunter.

Only explicit, machine-readable licence declarations or dedicated rights/licence
sections are accepted. A host being a government, archive, or school is not a licence.
Unknown or ambiguous pages are discovery-only and are not ingested.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse
from ipaddress import ip_address

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class OpenLicence:
    name: str
    url: str
    permits_research: bool
    permits_ai_training: bool
    permits_commercial_use: bool


_ALLOWED_MARKERS: tuple[tuple[tuple[str, ...], OpenLicence], ...] = (
    (("creativecommons.org/publicdomain/zero/1.0", "cc0 1.0", "cc0-1.0"),
     OpenLicence("CC0-1.0", "https://creativecommons.org/publicdomain/zero/1.0/", True, True, True)),
    (("creativecommons.org/licenses/by/4.0", "cc by 4.0", "cc-by-4.0"),
     OpenLicence("CC-BY-4.0", "https://creativecommons.org/licenses/by/4.0/", True, True, True)),
    (("creativecommons.org/licenses/by/3.0", "cc by 3.0", "cc-by-3.0"),
     OpenLicence("CC-BY-3.0", "https://creativecommons.org/licenses/by/3.0/", True, True, True)),
    (("public domain", "public-domain", "pd mark"),
     OpenLicence("Public Domain (explicitly stated)", "", True, True, True)),
    (("kenya open data license", "kenya open data licence", "government of kenya open data license"),
     OpenLicence("Kenya Open Data License (explicitly stated)", "", True, True, True)),
)


def detect_open_licence(html: str, page_url: str) -> OpenLicence | None:
    """Accept only an explicit licence link/meta field or dedicated rights section."""
    soup = BeautifulSoup(html, "lxml")
    candidates: list[tuple[str, str]] = []

    for tag in soup.find_all(["a", "link", "meta"]):
        rel = tag.get("rel", [])
        if isinstance(rel, str):
            rel = rel.lower().split()
        href = tag.get("href", "")
        content = tag.get("content", "")
        text = tag.get_text(" ", strip=True) if hasattr(tag, "get_text") else ""
        value = " ".join(str(part) for part in [href, content, text] if part)
        is_rights_field = (
            "license" in rel or "licence" in rel
            or tag.get("name", "").lower() in {"license", "licence", "dc.rights", "dcterms.license", "rights"}
            or tag.get("property", "").lower() in {"og:license", "dc.rights"}
        )
        if is_rights_field:
            candidates.append((value.lower(), urljoin(page_url, href) if href else ""))

    for selector in (".license", ".licence", "#license", "#licence", "[itemprop='license']"):
        for node in soup.select(selector):
            candidates.append((node.get_text(" ", strip=True).lower(), ""))

    for candidate, candidate_url in candidates:
        for markers, licence in _ALLOWED_MARKERS:
            if any(marker in candidate for marker in markers):
                return OpenLicence(
                    name=licence.name,
                    url=candidate_url or licence.url,
                    permits_research=licence.permits_research,
                    permits_ai_training=licence.permits_ai_training,
                    permits_commercial_use=licence.permits_commercial_use,
                )
    return None


def canonicalize_url(url: str) -> str:
    """Normalise URL identity for source and content deduplication."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.port and not ((scheme == "http" and parsed.port == 80) or (scheme == "https" and parsed.port == 443)):
        host = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunparse((scheme, host, path, "", parsed.query, ""))


def is_safe_http_url(url: str) -> bool:
    """Reject non-web schemes, credentialed URLs, and obvious local/private targets."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            return False
        if parsed.port is not None and parsed.port != (80 if parsed.scheme == "http" else 443):
            return False
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            return False
        try:
            address = ip_address(host)
            if not address.is_global:
                return False
        except ValueError:
            pass
        return True
    except (TypeError, ValueError):
        return False
