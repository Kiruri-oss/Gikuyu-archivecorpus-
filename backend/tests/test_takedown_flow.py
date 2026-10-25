import pytest
from sqlalchemy import select

from app.api.v1 import takedowns as takedown_module
from app.core.security import create_access_token, hash_password
from app.models.source import Source, SourceStatus, SourceType
from app.models.takedown import TakedownStatus
from app.models.text_record import TextRecord
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_takedown_request_hides_approved_source_and_action_removes_text(
    client, db_session, monkeypatch
):
    source = Source(
        url="https://publisher.example/gikuyu-text",
        domain="publisher.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
        license="CC-BY",
        raw_metadata="{}",
    )
    db_session.add(source)
    await db_session.flush()
    record = TextRecord(
        source_id=source.id,
        title="Gĩkũyũ text",
        body="Nĩguo mũciĩ wa mũndũ.",
        language_code="ki",
        sha256="e" * 64,
        license="CC-BY",
        allow_public_display=True,
        allow_research_use=True,
    )
    db_session.add(record)
    await db_session.commit()

    request_response = await client.post(
        "/api/v1/takedowns",
        json={
            "url": source.url,
            "requester_name": "Rights holder",
            "requester_email": "rights@example.com",
            "reason": "I am the rights holder and request removal of this material.",
        },
    )
    assert request_response.status_code == 201
    takedown_id = request_response.json()["id"]
    await db_session.refresh(source)
    assert source.status == SourceStatus.PENDING

    admin = User(
        email="archive-admin@example.com",
        full_name="Archive Admin",
        hashed_password=hash_password("SecureAdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token(str(admin.id), admin.role.value)

    async def no_index_delete(_index, _document_id):
        return None

    monkeypatch.setattr(takedown_module.search_index, "delete_document", no_index_delete)

    action_response = await client.post(
        f"/api/v1/takedowns/{takedown_id}/action",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert action_response.status_code == 200
    assert action_response.json()["status"] == TakedownStatus.ACTIONED.value

    await db_session.refresh(source)
    assert source.status == SourceStatus.TAKEN_DOWN
    remaining = await db_session.execute(select(TextRecord).where(TextRecord.source_id == source.id))
    assert remaining.scalars().all() == []


@pytest.mark.asyncio
async def test_takedown_keeps_media_row_when_object_storage_cleanup_fails(
    client, db_session, monkeypatch
):
    from app.models.media import Media, MediaKind

    source = Source(
        url="https://publisher.example/gikuyu-audio",
        domain="publisher.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
        license="CC-BY",
        raw_metadata="{}",
    )
    db_session.add(source)
    await db_session.flush()
    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        title="Gĩkũyũ recording",
        file_key="test/gikuyu-audio.wav",
        sha256="f" * 64,
        license="CC-BY",
        allow_public_display=True,
    )
    db_session.add(media)
    await db_session.commit()

    request_response = await client.post(
        "/api/v1/takedowns",
        json={
            "url": source.url,
            "requester_name": "Rights holder",
            "requester_email": "rights@example.com",
            "reason": "I own this recording and request its removal from the archive.",
        },
    )
    assert request_response.status_code == 201
    takedown_id = request_response.json()["id"]

    admin = User(
        email="cleanup-admin@example.com",
        full_name="Cleanup Admin",
        hashed_password=hash_password("SecureAdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token(str(admin.id), admin.role.value)

    async def no_index_delete(_index, _document_id):
        return None

    def failed_storage_delete(_bucket, _file_key):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(takedown_module.search_index, "delete_document", no_index_delete)
    monkeypatch.setattr(takedown_module.storage_service, "delete", failed_storage_delete)

    response = await client.post(
        f"/api/v1/takedowns/{takedown_id}/action",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == TakedownStatus.UNDER_REVIEW.value
    await db_session.refresh(source)
    assert source.status == SourceStatus.TAKEN_DOWN
    assert await db_session.get(Media, media.id) is not None


@pytest.mark.asyncio
async def test_rejecting_multiple_takedown_requests_restores_source_only_after_last_rejection(
    client, db_session
):
    source = Source(
        url="https://publisher.example/reported-text",
        domain="publisher.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
        license="CC-BY",
        raw_metadata="{}",
        reviewer_notes="original review note",
    )
    db_session.add(source)
    await db_session.commit()

    payload = {
        "url": source.url,
        "requester_name": "Rights holder",
        "requester_email": "rights@example.com",
        "reason": "I own this material and request its removal from the archive.",
    }
    first = await client.post("/api/v1/takedowns", json=payload)
    second = await client.post("/api/v1/takedowns", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201

    await db_session.refresh(source)
    assert source.status == SourceStatus.PENDING
    assert source.reviewer_notes.startswith("[takedown hold]")

    admin = User(
        email="multi-takedown-admin@example.com",
        full_name="Takedown Admin",
        hashed_password=hash_password("SecureAdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token(str(admin.id), admin.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    first_rejection = await client.post(
        f"/api/v1/takedowns/{first.json()['id']}/reject",
        headers=headers,
    )
    assert first_rejection.status_code == 200
    await db_session.refresh(source)
    assert source.status == SourceStatus.PENDING

    second_rejection = await client.post(
        f"/api/v1/takedowns/{second.json()['id']}/reject",
        headers=headers,
    )
    assert second_rejection.status_code == 200
    await db_session.refresh(source)
    assert source.status == SourceStatus.APPROVED
    assert source.reviewer_notes == "original review note"
