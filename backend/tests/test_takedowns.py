import pytest


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
async def test_takedown_request_immediately_hides_an_approved_source(client, db_session):
    from app.models.source import Source, SourceStatus, SourceType

    source = Source(
        url="https://archive.example/gikuyu-recording",
        domain="archive.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
    )
    db_session.add(source)
    await db_session.commit()

    response = await client.post("/api/v1/takedowns", json={
        "url": source.url,
        "requester_name": "Rights Holder",
        "requester_email": "rights@example.com",
        "reason": "I own this recording and request its removal from the archive.",
    })
    assert response.status_code == 201

    await db_session.refresh(source)
    assert source.status == SourceStatus.PENDING


@pytest.mark.asyncio
async def test_rejected_takedown_restores_source_hidden_only_for_that_request(client, db_session):
    from app.core.security import create_access_token, hash_password
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.user import User, UserRole

    admin = User(
        email="archive-admin@example.com",
        full_name="Archive Admin",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    source = Source(
        url="https://archive.example/restorable-record",
        domain="archive.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
    )
    db_session.add_all([admin, source])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(source)

    submitted = await client.post("/api/v1/takedowns", json={
        "url": source.url,
        "requester_name": "Requester",
        "requester_email": "requester@example.com",
        "reason": "I am authorised to report this record and request a review.",
    })
    assert submitted.status_code == 201
    await db_session.refresh(source)
    assert source.status == SourceStatus.PENDING

    token = create_access_token(str(admin.id), admin.role.value)
    rejected = await client.post(
        f"/api/v1/takedowns/{submitted.json()['id']}/reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rejected.status_code == 200
    await db_session.refresh(source)
    assert source.status == SourceStatus.APPROVED
    assert rejected.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_takedown_cleanup_failure_retains_hidden_media_for_retry(
    client, db_session, monkeypatch
):
    from app.api.v1 import takedowns as takedown_module
    from app.core.security import create_access_token, hash_password
    from app.models.media import Media, MediaKind
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.takedown import TakedownStatus
    from app.models.user import User, UserRole

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
    from app.core.security import create_access_token, hash_password
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.user import User, UserRole

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
