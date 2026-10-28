import hashlib
import json
import uuid

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.deps import DbSession, CurrentUser
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


@router.get("/me")
async def my_archive_summary(db: DbSession, user: CurrentUser) -> dict:
    """Return the signed-in user's own Gĩkũyũ contribution history and review state."""
    text_result = await db.execute(
        select(TextRecord, Source.status)
        .join(Source, TextRecord.source_id == Source.id)
        .where(TextRecord.contributor_id == user.id, TextRecord.language_code == "ki")
        .order_by(TextRecord.created_at.desc())
        .limit(200)
    )

    recent: list[dict] = []
    text_rows = text_result.all()
    for record, source_status in text_rows:
        recent.append({
            "id": str(record.id),
            "title": record.title,
            "kind": "text",
            "genre": record.genre,
            "status": source_status.value if hasattr(source_status, "value") else str(source_status),
            "created_at": record.created_at.isoformat() if record.created_at else "",
        })

    # Audio upload contributor identity is preserved in source provenance metadata.
    # Filter candidates in SQL, then verify the parsed JSON identity exactly.
    media_result = await db.execute(
        select(Media, Source.status, Source.raw_metadata)
        .join(Source, Media.source_id == Source.id)
        .where(
            Source.source_type == SourceType.USER_UPLOAD,
            Source.raw_metadata.contains(str(user.id)),
            Media.language_code == "ki",
        )
        .order_by(Media.created_at.desc())
        .limit(200)
    )
    for media, source_status, raw_metadata in media_result.all():
        try:
            metadata = json.loads(raw_metadata or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if str(metadata.get("contributor_id") or "") != str(user.id):
            continue
        recent.append({
            "id": str(media.id),
            "title": media.title,
            "kind": "audio",
            "genre": media.genre,
            "status": source_status.value if hasattr(source_status, "value") else str(source_status),
            "created_at": media.created_at.isoformat() if media.created_at else "",
        })

    recent.sort(key=lambda item: item["created_at"], reverse=True)
    totals = {
        "total": len(recent),
        "texts": sum(1 for item in recent if item["kind"] == "text"),
        "recordings": sum(1 for item in recent if item["kind"] == "audio"),
        "pending": sum(1 for item in recent if item["status"] == "pending"),
        "approved": sum(1 for item in recent if item["status"] == "approved"),
        "rejected": sum(1 for item in recent if item["status"] == "rejected"),
        "taken_down": sum(1 for item in recent if item["status"] == "taken_down"),
    }
    return {"totals": totals, "recent": recent[:30]}
