import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord
from app.services.indexing import search_index

logger = get_logger(__name__)

WIKIMEDIA_LICENSE = "CC BY-SA 4.0"
WIKIMEDIA_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
MAX_ARTICLE_CHARS = 20_000

LANGUAGE_WIKIS: dict[str, tuple[str, str]] = {
    # This is deliberately Gĩkũyũ-only. The archive is not a multilingual importer.
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


async def _get_random_pages(client: Any, host: str, limit: int) -> list[dict[str, Any]]:
    response = await client.get(
        f"https://{host}/w/api.php",
        params={
            "action": "query",
            "generator": "random",
            "grnnamespace": "0",
            "grnlimit": str(limit),
            "prop": "extracts|info|revisions",
            "explaintext": "1",
            "exchars": str(MAX_ARTICLE_CHARS),
            "inprop": "url",
            "rvprop": "ids|timestamp",
            "rvlimit": "1",
            "format": "json",
            "formatversion": "2",
        },
        headers={"User-Agent": "GikuyuLanguageArchive/1.0 (rights-aware community language archive)"},
    )
    response.raise_for_status()
    payload = response.json()
    pages = payload.get("query", {}).get("pages", [])
    if isinstance(pages, dict):
        pages = list(pages.values())
    return pages if isinstance(pages, list) else []


async def import_random_wikipedia_pages(
    db: AsyncSession,
    language_code: str,
    limit: int = 10,
    client: Any | None = None,
) -> ImportResult:
    code = language_code.strip().lower()
    if code not in LANGUAGE_WIKIS:
        raise ValueError(f"Unsupported language code: {language_code}")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")

    host, language_name = LANGUAGE_WIKIS[code]
    result = ImportResult(language_code=code, requested=limit)
    if client is None:
        async with httpx.AsyncClient(timeout=20.0) as http:
            pages = await _get_random_pages(http, host, limit)
    else:
        pages = await _get_random_pages(client, host, limit)

    for page in pages:
        title = str(page.get("title") or "").strip()
        body = re.sub(r"\n{3,}", "\n\n", str(page.get("extract") or "").strip())
        body = body[:MAX_ARTICLE_CHARS].strip()
        page_id = page.get("pageid")
        source_url = str(page.get("fullurl") or (f"https://{host}/?curid={page_id}" if page_id else "")).strip()
        if not title or len(body) < 80 or not source_url.startswith(f"https://{host}/"):
            result.skipped_empty += 1
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
            "provider": "Wikimedia",
            "project": host,
            "page_id": page_id,
            "revision_id": revision.get("revid"),
            "revision_timestamp": revision.get("timestamp"),
            "attribution": f"{title} — {language_name} Wikipedia contributors",
            "license": WIKIMEDIA_LICENSE,
            "license_url": WIKIMEDIA_LICENSE_URL,
            "retrieval_method": "MediaWiki API generator=random",
        }
        source = Source(
            url=source_url,
            domain=host,
            source_type=SourceType.WEB,
            status=SourceStatus.APPROVED,
            license=WIKIMEDIA_LICENSE,
            raw_metadata=json.dumps(metadata, ensure_ascii=False),
        )
        db.add(source)
        await db.flush()

        record = TextRecord(
            source_id=source.id,
            source=source,
            title=title,
            body=body,
            language_code=code,
            dialect=language_name,
            genre="encyclopedia article",
            sha256=digest,
            size_bytes=len(body.encode("utf-8")),
            license=WIKIMEDIA_LICENSE,
            allow_public_display=True,
            allow_research_use=True,
            # Do not treat public accessibility or a general content licence as automatic
            # consent for this project's model-training or commercial dataset products.
            allow_ai_training=False,
            allow_commercial_use=False,
            notes=f"Imported from {source_url}; verify attribution and current source licence before reuse.",
        )
        db.add(record)
        await db.flush()
        try:
            await search_index.index_document("texts", {
                "id": str(record.id),
                "title": record.title,
                "body": record.body,
                "language_code": record.language_code,
                "dialect": record.dialect or "",
                "genre": record.genre or "",
                "license": record.license,
                "source_url": source_url,
                "allow_ai_training": False,
                "allow_commercial_use": False,
            })
        except Exception as exc:
            logger.warning("wikimedia.import_index_failed", source_url=source_url, error=str(exc))
        result.imported += 1

    return result
