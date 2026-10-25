"""Explicit licence parsing and URL canonicalisation for the corpus hunter."""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class OpenLicence:
    name: str
    url: str
    permits_research: bool = True
    permits_ai_training: bool = True
    permits_commercial_use: bool = True


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().rstrip(".")
    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    return urlunparse((scheme, host, parsed.path or "/", "", parsed.query, ""))


def is_safe_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            return False
        if parsed.port is not None and parsed.port != (80 if parsed.scheme == "http" else 443):
            return False
        if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
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


def _cc_licence_from_url(url: str) -> OpenLicence | None:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.hostname not in {"creativecommons.org", "www.creativecommons.org"}:
        return None
    path = parsed.path.rstrip("/")
    accepted = {
        "/publicdomain/zero/1.0": OpenLicence("CC0", url),
        "/licenses/by/4.0": OpenLicence("CC-BY", url),
        "/licenses/by/3.0": OpenLicence("CC-BY", url),
    }
    return accepted.get(path)


def detect_open_licence(html: str, page_url: str) -> OpenLicence | None:
    """Accept explicit licence links/metadata or a dedicated licence section only."""
    soup = BeautifulSoup(html, "lxml")
    candidates: list[tuple[str, str]] = []

    for tag in soup.find_all(["a", "link", "meta"]):
        rel = tag.get("rel", [])
        if isinstance(rel, str):
            rel = rel.lower().split()
        href = str(tag.get("href", "") or "")
        content = str(tag.get("content", "") or "")
        label = " ".join(str(value) for value in (
            tag.get("title", ""), tag.get("aria-label", ""), tag.get("name", ""),
            tag.get("property", ""), content, tag.get_text(" ", strip=True)
        ) if value).lower()
        is_rights_field = (
            "license" in rel or "licence" in rel
            or str(tag.get("name", "")).lower() in {"license", "licence", "dc.rights", "dcterms.license", "rights"}
            or str(tag.get("property", "")).lower() in {"og:license", "dc.rights"}
        )
        if is_rights_field:
            candidates.append((label, urljoin(page_url, href) if href else ""))

    for selector in (".license", ".licence", "#license", "#licence", "[itemprop='license']"):
        for node in soup.select(selector):
            candidates.append((node.get_text(" ", strip=True).lower(), ""))

    for label, licence_url in candidates:
        cc_url = _cc_licence_from_url(licence_url)
        if cc_url:
            return cc_url
        if label.startswith(("http://", "https://")):
            cc_url = _cc_licence_from_url(label.split()[0])
            if cc_url:
                return cc_url
        compact = " ".join(label.replace("-", " ").split())
        if any(term in compact for term in ("cc0 1.0", "cc0", "public domain dedication")):
            return OpenLicence("CC0", licence_url or "https://creativecommons.org/publicdomain/zero/1.0/")
        if any(term in compact for term in ("cc by 4.0", "cc by 3.0", "cc by 4", "cc by 3")):
            # Attribution-only licences qualify; ShareAlike and NonCommercial do not.
            if "sharealike" not in compact and "share alike" not in compact and "noncommercial" not in compact and "non commercial" not in compact:
                return OpenLicence("CC-BY", licence_url)
        if any(term in compact for term in ("public domain", "public-domain")):
            return OpenLicence("PUBLIC-DOMAIN", licence_url)
        if any(term in compact for term in (
            "kenya open data license", "kenya open data licence",
            "government of kenya open data license", "government of kenya open data licence",
        )):
            return OpenLicence("KE-GOV-OPEN", licence_url, permits_research=True, permits_ai_training=False, permits_commercial_use=False)

    return None
