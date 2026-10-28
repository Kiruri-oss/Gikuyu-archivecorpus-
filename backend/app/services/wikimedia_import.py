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
    """Import the openly licensed Gĩkũyũ Bible in restartable, bounded batches."""
    existing_sources = await db.execute(
        select(Source.raw_metadata).where(Source.domain == "ebible.org")
    )
    for raw_metadata, in existing_sources.all():
        try:
            metadata = json.loads(raw_metadata or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if metadata.get("import_complete") is True:
            logger.info("bible.import_already_complete", imported_count=metadata.get("imported_count"))
            return {"imported": 0, "skipped": 1}

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=20.0), follow_redirects=True, headers={
            "User-Agent": "GikuyuArchiveCorpus/1.1 (openly licensed Gĩkũyũ text preservation)"
        })

    imported = 0
    skipped = 0
    candidate_count = 0
    batch_size = 40
    try:
        logger.info("bible.import_download_started", url=BIBLICA_DOWNLOAD)
        response = await client.get(BIBLICA_DOWNLOAD)
        response.raise_for_status()
        payload = response.content
        logger.info("bible.import_download_complete", bytes=len(payload))
        if not payload or len(payload) > MAX_BIBLE_ZIP_BYTES:
            raise ValueError(
                f"Bible archive size was outside the allowed range: {len(payload)} bytes"
            )

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            entries = [
                info for info in archive.infolist()
                if not info.is_dir()
                and info.filename.lower().endswith((".txt", ".usfm"))
                and 80 <= info.file_size <= 2_000_000
            ]
            logger.info(
                "bible.import_archive_inspected",
                archive_members=len(archive.infolist()),
                eligible_files=len(entries),
            )

            for offset in range(0, len(entries), batch_size):
                batch = entries[offset:offset + batch_size]
                urls = [
                    f"{BIBLICA_SOURCE}#file={info.filename}"
                    for info in batch
                ]
                existing_url_result = await db.execute(
                    select(Source.url).where(Source.url.in_(urls))
                )
                existing_urls = set(existing_url_result.scalars().all())

                eligible: list[tuple[Any, str, str, str, int]] = []
                for info in batch:
                    url = f"{BIBLICA_SOURCE}#file={info.filename}"
                    if url in existing_urls:
                        skipped += 1
                        continue

                    raw = archive.read(info)
                    body = raw.decode("utf-8-sig", errors="replace").strip()
                    body = re.sub(r"\n{3,}", "\n\n", body)
                    if len(body) < 80:
                        skipped += 1
                        continue

                    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
                    eligible.append((info, url, body, digest, len(raw)))

                # Duplicate hash checks are batched as well. The unique constraint
                # remains the final guard against concurrent import workers.
                digests = [entry[3] for entry in eligible]
                existing_digest_result = await db.execute(
                    select(TextRecord.sha256).where(TextRecord.sha256.in_(digests))
                ) if digests else None
                existing_digests = (
                    set(existing_digest_result.scalars().all())
                    if existing_digest_result is not None else set()
                )

                new_entries = []
                seen_in_batch: set[str] = set()
                for info, url, body, digest, size_bytes in eligible:
                    if digest in existing_digests or digest in seen_in_batch:
                        skipped += 1
                        continue
                    seen_in_batch.add(digest)
                    name = info.filename
                    title = name.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ").strip()
                    metadata = {
                        "provider": "Biblica via eBible.org",
                        "work": "Biblica® Kiugo Gĩtheru Kĩa Ngai Kĩhingũre",
                        "language": "Gĩkũyũ (ki)",
                        "contributor": "Biblica, Inc.",
                        "copyright": "© 2013 Biblica, Inc.",
                        "license": BIBLICA_LICENSE,
                        "license_url": BIBLICA_LICENSE_URL,
                        "source_url": BIBLICA_SOURCE,
                        "download_url": BIBLICA_DOWNLOAD,
                        "archive_member": name,
                        "attribution": "Original work by Biblica, Inc.; available at www.biblica.com and open.bible.",
                        "changes": "Text extracted from the publisher-provided plain-text archive; formatting may differ from the source edition.",
                    }
                    source = Source(
                        url=url,
                        domain="ebible.org",
                        source_type=SourceType.BOOK,
                        status=SourceStatus.APPROVED,
                        license=BIBLICA_LICENSE,
                        language_confidence=1.0,
                        raw_metadata=json.dumps(metadata, ensure_ascii=False),
                    )
                    new_entries.append((source, title, body, digest, size_bytes))

                if new_entries:
                    db.add_all([entry[0] for entry in new_entries])
                    # One database flush for the batch, not per chapter.
                    await db.flush()
                    records = []
                    for source, title, body, digest, size_bytes in new_entries:
                        records.append(TextRecord(
                            source_id=source.id,
                            source=source,
                            title=f"Gĩkũyũ Bible — {title}",
                            author="Biblica, Inc.",
                            year=2013,
                            body=body,
                            language_code="ki",
                            dialect="Gĩkũyũ",
                            genre="Bible / religious literature",
                            sha256=digest,
                            size_bytes=size_bytes,
                            lang_score=1.0,
                            license=BIBLICA_LICENSE,
                            allow_public_display=True,
                            allow_research_use=True,
                            allow_ai_training=False,
                            allow_commercial_use=False,
                            notes=f"eBible.org openly licensed Gĩkũyũ text. CC BY-SA 4.0; attribution retained. Source: {BIBLICA_SOURCE}",
                        ))
                    db.add_all(records)
                    await db.flush()
                    await db.commit()
                    imported += len(records)

                    try:
                        await search_index.index_documents("texts", [
                            {
                                "id": str(record.id),
                                "title": record.title,
                                "body": record.body,
                                "language_code": "ki",
                                "dialect": "Gĩkũyũ",
                                "genre": record.genre or "",
                                "license": BIBLICA_LICENSE,
                                "source_url": BIBLICA_SOURCE,
                                "allow_ai_training": False,
                                "allow_commercial_use": False,
                            }
                            for record in records
                        ])
                    except Exception as exc:
                        logger.warning(
                            "bible.import_index_failed",
                            batch_size=len(records),
                            error=str(exc),
                        )

                candidate_count += len(batch)
                if candidate_count % 200 == 0 or candidate_count == len(entries):
                    logger.info(
                        "bible.import_progress",
                        inspected=candidate_count,
                        eligible_files=len(entries),
                        imported=imported,
                        skipped=skipped,
                    )

        # Mark the import complete in the provenance of the last source record.
        # This avoids downloading and reprocessing the full archive on every restart.
        last_source_result = await db.execute(
            select(Source).where(Source.domain == "ebible.org").order_by(Source.created_at.desc()).limit(1)
        )
        last_source = last_source_result.scalar_one_or_none()
        if last_source is not None:
            try:
                final_metadata = json.loads(last_source.raw_metadata or "{}")
            except (TypeError, json.JSONDecodeError):
                final_metadata = {}
            final_metadata["import_complete"] = True
            final_metadata["new_records_added"] = imported
            final_metadata["archive_members_processed"] = candidate_count
            last_source.raw_metadata = json.dumps(final_metadata, ensure_ascii=False)
            await db.commit()

        logger.info("bible.import_finished", imported=imported, skipped=skipped, inspected=candidate_count)
        return {"imported": imported, "skipped": skipped}
    except Exception:
        await db.rollback()
        logger.exception("bible.import_failed", imported=imported, skipped=skipped, inspected=candidate_count)
        raise
    finally:
        if own_client:
            await client.aclose()
