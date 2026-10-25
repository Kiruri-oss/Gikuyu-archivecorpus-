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
