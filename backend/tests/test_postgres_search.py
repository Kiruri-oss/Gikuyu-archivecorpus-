import uuid

import pytest

from app.models.media import Media, MediaKind
from app.models.segment import Segment
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord


@pytest.mark.asyncio
async def test_search_returns_only_approved_public_corpus_records(client, db_session):
    approved = Source(
        url="https://example.org/gikuyu-corpus",
        domain="example.org",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.APPROVED,
        license="CC0",
    )
    pending = Source(
        url="https://example.org/pending",
        domain="example.org",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.PENDING,
        license="CC0",
    )
    db_session.add_all([approved, pending])
    await db_session.flush()

    db_session.add_all([
        TextRecord(
            source_id=approved.id,
            title="Oral tradition",
            body="Gĩkũyũ words preserve community memory.",
            language_code="ki",
            sha256=uuid.uuid4().hex,
            license="CC0",
            allow_public_display=True,
            allow_research_use=True,
        ),
        TextRecord(
            source_id=pending.id,
            title="Gĩkũyũ pending text",
            body="Gĩkũyũ pending content must not appear.",
            language_code="ki",
            sha256=uuid.uuid4().hex,
            license="CC0",
            allow_public_display=True,
            allow_research_use=True,
        ),
    ])

    media = Media(
        source_id=approved.id,
        kind=MediaKind.AUDIO,
        title="Gĩkũyũ oral story",
        file_key="private/audio-object",
        sha256=uuid.uuid4().hex,
        dialect="Ki-Murang'a",
        license="CC0",
        allow_public_display=True,
        allow_research_use=True,
    )
    db_session.add(media)
    await db_session.flush()
    db_session.add(Segment(
        media_id=media.id,
        start_seconds=0,
        end_seconds=3,
        transcript="Gĩkũyũ oral tradition.",
        translation="Gikuyu oral tradition.",
    ))
    await db_session.commit()

    response = await client.get("/api/v1/search", params={"q": "Gĩkũyũ"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["media"]) == 1
    assert len(payload["segments"]) == 1
    assert len(payload["texts"]) == 1
    assert payload["texts"][0]["source_url"] == "https://example.org/gikuyu-corpus"
    assert "pending" not in payload["texts"][0]["title"].lower()

    browse = await client.get("/api/v1/search")
    assert browse.status_code == 200
    assert browse.json()["source"] == "archive_corpus"
    assert len(browse.json()["texts"]) == 1


@pytest.mark.asyncio
async def test_search_rejects_whitespace_only_query(client):
    response = await client.get("/api/v1/search", params={"q": "   "})
    assert response.status_code in {400, 422}
