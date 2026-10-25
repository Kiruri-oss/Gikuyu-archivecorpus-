import hashlib
import json
import uuid

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.deps import DbSession
from app.models.media import Media, MediaKind
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord

router = APIRouter(prefix="/community", tags=["community"])


def _display_name(contributor_id: str) -> str:
    digest = hashlib.sha256(contributor_id.encode("utf-8")).hexdigest()[:6].upper()
    return f"Contributor {digest}"


@router.get("/leaderboard")
async def contributor_leaderboard(
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    """Rank contributors by approved, publicly displayable Gĩkũyũ records.

    Names and email addresses are not exposed. Audio contributor IDs are read
    from the consent/provenance metadata stored with each approved upload.
    """
    counts: dict[str, dict[str, int]] = {}

    text_result = await db.execute(
        select(TextRecord.contributor_id, func.count(TextRecord.id))
        .join(Source, TextRecord.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            TextRecord.allow_public_display.is_(True),
            TextRecord.contributor_id.is_not(None),
            TextRecord.language_code == "ki",
        )
        .group_by(TextRecord.contributor_id)
    )
    for contributor_id, total in text_result.all():
        key = str(contributor_id)
        counts.setdefault(key, {"texts": 0, "recordings": 0})
        counts[key]["texts"] += int(total)

    audio_result = await db.execute(
        select(Source.raw_metadata)
        .join(Media, Media.source_id == Source.id)
        .where(
            Source.status == SourceStatus.APPROVED,
            Source.source_type == SourceType.USER_UPLOAD,
            Media.kind == MediaKind.AUDIO,
            Media.allow_public_display.is_(True),
        )
    )
    for raw_metadata, in audio_result.all():
        try:
            metadata = json.loads(raw_metadata or "{}")
            contributor_id = str(metadata.get("contributor_id") or "")
            uuid.UUID(contributor_id)
        except (TypeError, ValueError, AttributeError, json.JSONDecodeError):
            continue
        counts.setdefault(contributor_id, {"texts": 0, "recordings": 0})
        counts[contributor_id]["recordings"] += 1

    ranked = []
    for contributor_id, contribution_counts in counts.items():
        total = contribution_counts["texts"] + contribution_counts["recordings"]
        if total < 1:
            continue
        ranked.append({
            "display_name": _display_name(contributor_id),
            "approved_contributions": total,
            "texts": contribution_counts["texts"],
            "recordings": contribution_counts["recordings"],
        })
    ranked.sort(key=lambda item: (-item["approved_contributions"], item["display_name"]))
    return {"items": [{"rank": index + 1, **item} for index, item in enumerate(ranked[:limit])]}
