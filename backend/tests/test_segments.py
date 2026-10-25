import pytest
import uuid
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_create_segment_validates_time_order(client, db_session, auth_headers):
    from app.models.media import Media, MediaKind
    from app.models.source import Source, SourceType

    source = Source(url="test://segment", domain="test", source_type=SourceType.USER_UPLOAD)
    db_session.add(source)
    await db_session.flush()
    media = Media(
        source_id=source.id, kind=MediaKind.AUDIO, title="Test",
        file_key="k", sha256=uuid.uuid4().hex, lang_score=0.9,
    )
    db_session.add(media)
    await db_session.commit()

    resp = await client.post("/api/v1/segments", json={
        "media_id": str(media.id),
        "start_seconds": 10.0,
        "end_seconds": 5.0,
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_segment_succeeds(client, db_session, auth_headers):
    from app.models.media import Media, MediaKind
    from app.models.source import Source, SourceType

    source = Source(url="test://segment2", domain="test", source_type=SourceType.USER_UPLOAD)
    db_session.add(source)
    await db_session.flush()
    media = Media(
        source_id=source.id, kind=MediaKind.AUDIO, title="Test2",
        file_key="k2", sha256=uuid.uuid4().hex, lang_score=0.9,
    )
    db_session.add(media)
    await db_session.commit()

    with patch(
        "app.api.v1.segments.search_index.index_document",
        new_callable=AsyncMock,
        side_effect=RuntimeError("search index unavailable"),
    ) as mock_index:
        resp = await client.post("/api/v1/segments", json={
            "media_id": str(media.id),
            "start_seconds": 0.0,
            "end_seconds": 5.0,
            "transcript": "Nĩ ũndũ mwega",
        }, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["transcript"] == "Nĩ ũndũ mwega"
    mock_index.assert_awaited_once()