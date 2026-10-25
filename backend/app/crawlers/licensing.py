"""Conservative licence detection for the automatic corpus hunter.

Only explicit, machine-readable or clearly stated licences are accepted. A host
being a government, archive, or educational institution is not itself a licence.
Unknown and ambiguous pages are discovery-only and must not be archived.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class OpenLicence:
    name: str
    url: str
    permits_research: bool
    permits_ai_training: bool
    permits_commercial_use: bool


_ALLOWED_MARKERS: tuple[tuple[tuple[str, ...], OpenLicence], ...] = (
    (
        ("creativecommons.org/publicdomain/zero/1.0", "cc0 1.0", "cc0-1.0"),
        OpenLicence("CC0-1.0", "https://creativecommons.org/publicdomain/zero/1.0/", True, True, True),
    ),
    (
        ("creativecommons.org/licenses/by/4.0", "cc by 4.0", "cc-by-4.0"),
        OpenLicence("CC-BY-4.0", "https://creativecommons.org/licenses/by/4.0/", True, True, True),
    ),
    (
        ("creativecommons.org/licenses/by/3.0", "cc by 3.0", "cc-by-3.0"),
        OpenLicence("CC-BY-3.0", "https://creativecommons.org/licenses/by/3.0/", True, True, True),
    ),
    (
        ("public domain", "public-domain", "pd mark"),
        OpenLicence("Public Domain (explicitly stated)", "", True, True, True),
    ),
    (
        ("kenya open data license", "kenya open data licence", "government of kenya open data license"),
        OpenLicence("Kenya Open Data License (explicitly stated)", "", True, True, True),
    ),
)


def detect_open_licence(html: str, page_url: str) -> OpenLicence | None:
    """Return an approved licence only when the page explicitly identifies it."""
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
        if "license" in rel or "licence" in rel or tag.get("name", "").lower() in {
            "license", "licence", "dc.rights", "dcterms.license", "rights"
        } or tag.get("property", "").lower() in {"og:license", "dc.rights"}:
            candidates.append((value.lower(), urljoin(page_url, href) if href else ""))

    # Explicit page text is useful when a publisher states its rights without
    # machine-readable metadata. Generic "open access" claims are not accepted.
    visible_text = soup.get_text(" ", strip=True).lower()
    candidates.append((visible_text, ""))

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


def is_safe_http_url(url: str) -> bool:
    """Reject non-web schemes and obvious local/private targets before fetching."""
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            return False
        if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
            return False
        if host in {"127.0.0.1", "::1", "0.0.0.0", "169.254.169.254"}:
            return False
        return True
    except (TypeError, ValueError):
        return False
