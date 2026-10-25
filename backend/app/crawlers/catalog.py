"""Curated discovery seeds for Gĩkũyũ datasets.

These entries register source metadata only. They do not download gated files or
claim that a dataset is cleared for every downstream use. A reviewer must verify
the current source terms before approving a record for use.
"""

from __future__ import annotations

import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source, SourceStatus, SourceType

CURATED_SOURCES = [
    {
        "url": "https://curl.corpora.uni-leipzig.de/languages/kik",
        "title": "Leipzig Corpora Collection — Gikuyu",
        "license": "CC-BY (reported; verify current licence bundle)",
        "access": "public catalogue; verify download terms",
        "kind": "text_corpus",
        "language": "ki",
        "reason": "Published Gikuyu corpus catalogue; retain source provenance and verify item-specific terms.",
    },
    {
        "url": "https://huggingface.co/datasets/Professor/kikuyu-speech-data",
        "title": "Kikuyu Speech Data (Pooled)",
        "license": "CC-BY-4.0 (reported by dataset card)",
        "access": "gated; access request required",
        "kind": "audio_text_dataset",
        "language": "ki",
        "reason": "Register metadata only; do not download or bypass access controls before access is granted.",
    },
    {
        "url": "https://mcaai.maseno.ac.ke/datasets/afrivoices-ke-multilingual-speech-dataset-for-kenyan-languages",
        "title": "AfriVoices-KE / African Next Voices",
        "license": "CC-BY / NOODL terms reported; verify the governing agreement",
        "access": "publisher terms and access conditions require review",
        "kind": "multilingual_audio_text_dataset",
        "language": "ki",
        "reason": "Kikuyu is one of several languages; register metadata only until terms and access are verified.",
    },
]


async def seed_curated_sources(db: AsyncSession) -> int:
    """Insert missing source metadata as pending; never fetch or copy dataset contents."""
    created = 0
    for entry in CURATED_SOURCES:
        existing = await db.execute(select(Source.id).where(Source.url == entry["url"]))
        if existing.scalar_one_or_none():
            continue
        source = Source(
            url=entry["url"],
            domain=entry["url"].split("/", 3)[2].lower(),
            source_type=SourceType.WEB,
            status=SourceStatus.PENDING,
            license=entry["license"][:100],
            raw_metadata=json.dumps({
                "catalog_title": entry["title"],
                "catalog_kind": entry["kind"],
                "language": entry["language"],
                "access": entry["access"],
                "rights_state": "pending_human_verification",
                "notes": entry["reason"],
            }, ensure_ascii=False),
        )
        db.add(source)
        created += 1
    if created:
        await db.flush()
    return created
