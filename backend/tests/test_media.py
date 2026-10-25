import io
import json
import uuid
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_upload_media_creates_record(client, db_session, auth_headers):
    with patch("app.api.v1.media.storage_service.upload", return_value="test/key") as mock_upload, \
         patch("app.api.v1.media.search_index.index_document", new_callable=AsyncMock) as mock_index:
        payload = json.dumps({"title": "Ngano ya Njũkĩ", "speaker": "Wanjiku", "dialect": "Ki-Muranga", "license": "CC BY 4.0", "consent_to_archive": True, "confirm_rights": True, "consent_to_publish": True, "allow_research_use": True, "allow_ai_training": False, "allow_commercial_use": False})
        files = {"file": ("clip.webm", io.BytesIO(b"fake-audio-bytes"), "audio/webm")}
        resp = await client.post(
            "/api/v1/media",
            data={"meta": payload},
            files=files,
            headers=auth_headers,
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Ngano ya Njũkĩ"
    assert body["speaker"] == "Wanjiku"
    assert "file_url" in body
    mock_upload.assert_called_once()
    assert body["review_status"] == "pending"
    mock_index.assert_not_called()


@pytest.mark.asyncio
async def test_upload_media_rejects_duplicate(client, db_session, auth_headers):
    from app.models.media import Media, MediaKind
    from app.models.source import Source, SourceType

    source = Source(url="test://dup", domain="test", source_type=SourceType.USER_UPLOAD)
    db_session.add(source)
    await db_session.flush()

    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        title="Dup",
        file_key="dup/key",
        sha256="a" * 64,
    )
    db_session.add(media)
    await db_session.commit()

    payload = json.dumps({"title": "Dup title", "license": "CC BY 4.0", "consent_to_archive": True, "confirm_rights": True})
    files = {"file": ("clip.webm", io.BytesIO(b"fake-audio-bytes"), "audio/webm")}

    with patch("app.api.v1.media.storage_service.compute_sha256", return_value="a" * 64):
        resp = await client.post(
            "/api/v1/media",
            data={"meta": payload},
            files=files,
            headers=auth_headers,
        )

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_upload_media_rejects_oversized(client, auth_headers):
    from app.core.config import get_settings

    settings = get_settings()
    huge = b"x" * (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)

    payload = json.dumps({"title": "Huge", "license": "CC BY 4.0", "consent_to_archive": True, "confirm_rights": True})
    files = {"file": ("clip.webm", io.BytesIO(huge), "audio/webm")}

    resp = await client.post(
        "/api/v1/media",
        data={"meta": payload},
        files=files,
        headers=auth_headers,
    )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_list_media_filters_by_dialect(client, db_session, auth_headers):
    from app.models.media import Media, MediaKind
    from app.models.source import Source, SourceType

    source = Source(url="test://list", domain="test", source_type=SourceType.USER_UPLOAD, status=__import__("app.models.source", fromlist=["SourceStatus"]).SourceStatus.APPROVED)
    db_session.add(source)
    await db_session.flush()

    db_session.add_all([
        Media(source_id=source.id, kind=MediaKind.AUDIO, title="A", file_key="k1",
              sha256=uuid.uuid4().hex, dialect="Ki-Muranga", allow_public_display=True),
        Media(source_id=source.id, kind=MediaKind.AUDIO, title="B", file_key="k2",
              sha256=uuid.uuid4().hex, dialect="Ki-Nyeri", allow_public_display=True),
    ])
    await db_session.commit()

    resp = await client.get("/api/v1/media?dialect=Ki-Muranga")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "A"

@pytest.mark.asyncio
async def test_get_media_returns_signed_url(client, db_session):
    from app.models.media import Media, MediaKind
    from app.models.source import Source, SourceType

    source = Source(url="test://detail", domain="test", source_type=SourceType.USER_UPLOAD, status=__import__("app.models.source", fromlist=["SourceStatus"]).SourceStatus.APPROVED)
    db_session.add(source)
    await db_session.flush()
    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        title="Detail test",
        file_key="detail/key",
        sha256=uuid.uuid4().hex,
        allow_public_display=True,
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(media)

    with patch("app.api.v1.media.storage_service.presigned_url", return_value="https://storage.example/audio") as mock_url:
        response = await client.get(f"/api/v1/media/{media.id}")

    assert response.status_code == 200
    assert response.json()["file_url"] == "https://storage.example/audio"
    mock_url.assert_called_once()
