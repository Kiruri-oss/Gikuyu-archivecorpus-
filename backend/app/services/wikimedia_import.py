import asyncio
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord
from app.services.indexing import search_index
from app.services.language_detector import language_detector

logger = get_logger(__name__)

WIKIMEDIA_LICENSE = "CC BY-SA 4.0"
WIKIMEDIA_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
BIBLICA_LICENSE = "CC BY-SA 4.0"
BIBLICA_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
BIBLICA_SOURCE = "https://ebible.org/bible/details.php?id=kik"
BIBLICA_DOWNLOAD = "https://ebible.org/Scriptures/kik_readaloud.zip"
MAX_ARTICLE_CHARS = 20_000
MAX_BIBLE_ZIP_BYTES = 30 * 1024 * 1024

LANGUAGE_WIKIS: dict[str, tuple[str, str]] = {
    "ki": ("ki.wikipedia.org", "Gĩkũyũ"),
}


@dataclass
class ImportResult:
    language_code: str
    requested: int
    imported: int = 0
    skipped_existing_source: int = 0
    skipped_duplicate_text: int = 0
    skipped_empty: int = 0
    skipped_non_gikuyu: int = 0


async def _get_random_pages(client: Any, host: str, limit: int) -> list[dict[str, Any]]:
    response = await client.get(
        f"https://{host}/w/api.php",
        params={
            "action": "query", "generator": "random", "grnnamespace": "0",
            "grnlimit": str(limit), "prop": "extracts|info|revisions",
            "explaintext": "1", "exchars": str(MAX_ARTICLE_CHARS), "inprop": "url",
            "rvprop": "ids|timestamp", "rvlimit": "1", "format": "json", "formatversion": "2",
        },
        headers={"User-Agent": "GikuyuLanguageArchive/1.1 (community language archive; contact: archive maintainers)"},
    )
    response.raise_for_status()
    payload = response.json()
    pages = payload.get("query", {}).get("pages", [])
    if isinstance(pages, dict):
        pages = list(pages.values())
    return pages if isinstance(pages, list) else []


async def import_random_wikipedia_pages(
    db: AsyncSession, language_code: str, limit: int = 10, client: Any | None = None
) -> ImportResult:
    code = language_code.strip().lower()
    if code not in LANGUAGE_WIKIS:
        raise ValueError(f"Unsupported language code: {language_code}")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    host, language_name = LANGUAGE_WIKIS[code]
    result = ImportResult(language_code=code, requested=limit)
    if client is None:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
            pages = await _get_random_pages(http, host, limit)
    else:
        pages = await _get_random_pages(client, host, limit)

    for page in pages:
        title = str(page.get("title") or "").strip()
        body = re.sub(r"\n{3,}", "\n\n", str(page.get("extract") or "").strip())[:MAX_ARTICLE_CHARS].strip()
        page_id = page.get("pageid")
        source_url = str(page.get("fullurl") or (f"https://{host}/?curid={page_id}" if page_id else "")).strip()
        if not title or len(body) < 80 or not source_url.startswith(f"https://{host}/"):
            result.skipped_empty += 1
            continue
        detected_language, confidence = language_detector.detect(body)
        if detected_language != "ki" or confidence < 0.55:
            result.skipped_non_gikuyu += 1
            continue
        existing_source = await db.execute(select(Source.id).where(Source.url == source_url))
        if existing_source.scalar_one_or_none():
            result.skipped_existing_source += 1
            continue
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        existing_text = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
        if existing_text.scalar_one_or_none():
            result.skipped_duplicate_text += 1
            continue
        revisions = page.get("revisions") or []
        revision = revisions[0] if revisions and isinstance(revisions[0], dict) else {}
        metadata = {
            "provider": "Wikimedia", "project": host, "page_id": page_id,
            "revision_id": revision.get("revid"), "revision_timestamp": revision.get("timestamp"),
            "attribution": f"{title} — {language_name} Wikipedia contributors",
            "license": WIKIMEDIA_LICENSE, "license_url": WIKIMEDIA_LICENSE_URL,
            "retrieval_method": "MediaWiki API generator=random",
            "language_detection": {"language": detected_language, "confidence": confidence},
        }
        source = Source(url=source_url, domain=host, source_type=SourceType.WEB,
                        status=SourceStatus.APPROVED, license=WIKIMEDIA_LICENSE,
                        raw_metadata=json.dumps(metadata, ensure_ascii=False))
        db.add(source)
        await db.flush()
        record = TextRecord(
            source_id=source.id, source=source, title=title, body=body, language_code=code,
            dialect=language_name, genre="encyclopedia article", sha256=digest,
            size_bytes=len(body.encode("utf-8")), license=WIKIMEDIA_LICENSE,
            allow_public_display=True, allow_research_use=True, allow_ai_training=False,
            allow_commercial_use=False, lang_score=confidence,
            notes=f"Imported from {source_url}; language filter passed ({confidence:.2f}). CC BY-SA attribution retained.",
        )
        db.add(record)
        await db.flush()
        try:
            await search_index.index_document("texts", {
                "id": str(record.id), "title": record.title, "body": record.body,
                "language_code": record.language_code, "dialect": record.dialect or "",
                "genre": record.genre or "", "license": record.license, "source_url": source_url,
                "allow_ai_training": False, "allow_commercial_use": False,
            })
        except Exception as exc:
            logger.warning("wikimedia.import_index_failed", source_url=source_url, error=str(exc))
        result.imported += 1
    return result


async def import_gikuyu_bible(db: AsyncSession, client: Any | None = None) -> dict[str, int]:
    """Import the openly licensed Gĩkũyũ Bible chapter-by-chapter with attribution."""
    existing = await db.execute(select(TextRecord.id).where(TextRecord.notes.like("%eBible.org%")).limit(1))
    if existing.scalar_one_or_none():
        return {"imported": 0, "skipped": 1}
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers={
            "User-Agent": "GikuyuArchiveCorpus/1.0 (openly licensed Gikuyu text preservation)"
        })
    try:
        response = await client.get(BIBLICA_DOWNLOAD)
        response.raise_for_status()
        payload = response.content
        if len(payload) > MAX_BIBLE_ZIP_BYTES:
            raise ValueError("Bible archive exceeded the configured download limit")
        imported = 0
        skipped = 0
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for info in archive.infolist():
                name = info.filename
                if info.is_dir() or not name.lower().endswith((".txt", ".usfm")):
                    continue
                if info.file_size > 2_000_000:
                    continue
                raw = archive.read(info)
                body = raw.decode("utf-8-sig", errors="replace").strip()
                body = re.sub(r"\n{3,}", "\n\n", body)
                if len(body) < 80:
                    continue
                # Files in this explicitly Kikuyu-only publisher package are Gĩkũyũ;
                # retain the original source and CC BY-SA notice on every chapter/section.
                title = name.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ").strip()
                url = f"{BIBLICA_SOURCE}#file={name}"
                exists = await db.execute(select(Source.id).where(Source.url == url))
                if exists.scalar_one_or_none():
                    skipped += 1
                    continue
                digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                duplicate = await db.execute(select(TextRecord.id).where(TextRecord.sha256 == digest))
                if duplicate.scalar_one_or_none():
                    skipped += 1
                    continue
                metadata = {
                    "provider": "Biblica via eBible.org",
                    "work": "Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre",
                    "language": "Gĩkũyũ (ki)", "contributor": "Biblica, Inc.",
                    "copyright": "© 2013 Biblica, Inc.", "license": BIBLICA_LICENSE,
                    "license_url": BIBLICA_LICENSE_URL, "source_url": BIBLICA_SOURCE,
                    "download_url": BIBLICA_DOWNLOAD, "archive_member": name,
                    "attribution": "Original work by Biblica, Inc.; available at www.biblica.com and open.bible.",
                    "changes": "Text extracted from the publisher-provided plain-text archive; formatting may differ from the source edition.",
                }
                source = Source(url=url, domain="ebible.org", source_type=SourceType.BOOK,
                                status=SourceStatus.APPROVED, license=BIBLICA_LICENSE,
                                language_confidence=1.0,
                                raw_metadata=json.dumps(metadata, ensure_ascii=False))
                db.add(source)
                await db.flush()
                record = TextRecord(
                    source_id=source.id, source=source, title=f"Gĩkũyũ Bible — {title}",
                    author="Biblica, Inc.", year=2013, body=body, language_code="ki",
                    dialect="Gĩkũyũ", genre="Bible / religious literature",
                    sha256=digest, size_bytes=len(raw), lang_score=1.0, license=BIBLICA_LICENSE,
                    allow_public_display=True, allow_research_use=True,
                    allow_ai_training=False, allow_commercial_use=False,
                    notes=f"eBible.org openly licensed Gĩkũyũ text. CC BY-SA 4.0; attribution retained. Source: {BIBLICA_SOURCE}",
                )
                db.add(record)
                await db.flush()
                try:
                    await search_index.index_document("texts", {
                        "id": str(record.id), "title": record.title, "body": record.body,
                        "language_code": "ki", "dialect": "Gĩkũyũ",
                        "genre": record.genre or "", "license": BIBLICA_LICENSE,
                        "source_url": BIBLICA_SOURCE, "allow_ai_training": False,
                        "allow_commercial_use": False,
                    })
                except Exception as exc:
                    logger.warning("bible.import_index_failed", source_url=url, error=str(exc))
                imported += 1
        await db.commit()
        return {"imported": imported, "skipped": skipped}
    finally:
        if own_client:
            await client.aclose()
