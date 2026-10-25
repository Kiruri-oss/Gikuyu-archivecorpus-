import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.security import create_access_token, hash_password
from app.models.media import Media, MediaKind
from app.models.segment import Segment
from app.models.source import Source, SourceStatus, SourceType
from app.models.takedown import Takedown, TakedownStatus
from app.models.text_record import TextRecord
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_takedown_submission_is_public(client):
    resp = await client.post("/api/v1/takedowns", json={
        "url": "https://example.com/audio.mp3",
        "requester_name": "Rights Holder",
        "requester_email": "rights@example.com",
        "reason": "This recording is my copyrighted work and was uploaded without permission.",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "received"


@pytest.mark.asyncio
async def test_takedown_rejects_invalid_email(client):
    resp = await client.post("/api/v1/takedowns", json={
        "url": "https://example.com/x",
        "requester_name": "X",
        "requester_email": "not-an-email",
        "reason": "short",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_actioned_takedown_hides_source_and_removes_archived_text_and_media(
    client, db_session
):
    admin = User(
        email="archive-admin@example.com",
        full_name="Archive Admin",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    source = Source(
        url="https://rights.example/gikuyu-record",
        domain="rights.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
        license="CC-BY",
    )
    db_session.add(source)
    await db_session.flush()

    text = TextRecord(
        source_id=source.id,
        title="Gĩkũyũ text",
        body="Mũciĩ nĩ ũhoro wa andũ.",
        language_code="ki",
        sha256=uuid.uuid4().hex,
        license="CC-BY",
        allow_public_display=True,
        allow_research_use=True,
    )
    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        title="Gĩkũyũ recording",
        file_key="test/gikuyu-audio",
        sha256=uuid.uuid4().hex,
        license="CC-BY",
        allow_public_display=True,
        allow_research_use=True,
    )
    db_session.add_all([text, media])
    await db_session.flush()
    segment = Segment(
        media_id=media.id,
        start_seconds=0,
        end_seconds=1,
        transcript="Mũciĩ",
        is_verified=True,
    )
    complaint = Takedown(
        url=source.url,
        requester_name="Rights Holder",
        requester_email="rights@example.com",
        reason="This is my copyrighted work and I did not authorise its republication.",
        status=TakedownStatus.RECEIVED,
    )
    db_session.add_all([segment, complaint])
    await db_session.commit()

    headers = {
        "Authorization": "Bearer " + create_access_token(str(admin.id), UserRole.ADMIN.value)
    }
    with patch("app.api.v1.takedowns.search_index.delete_document", new_callable=AsyncMock), \
         patch("app.api.v1.takedowns.storage_service.delete") as storage_delete:
        response = await client.post(
            f"/api/v1/takedowns/{complaint.id}/action", headers=headers
        )

    assert response.status_code == 200
    assert response.json()["status"] == "actioned"
    storage_delete.assert_called_once()
    assert await db_session.get(TextRecord, text.id) is None
    assert await db_session.get(Media, media.id) is None
    assert await db_session.get(Segment, segment.id) is None
    await db_session.refresh(source)
    assert source.status == SourceStatus.TAKEN_DOWN
