import json

import pytest

from app.models.source import Source, SourceStatus, SourceType


@pytest.mark.asyncio
async def test_public_reference_index_shows_only_gikuyu_metadata_only_sources(client, db_session):
    restricted = Source(
        url="https://youtube.com/watch?v=gikuyu-example",
        domain="youtube.com",
        source_type=SourceType.YOUTUBE,
        status=SourceStatus.PENDING,
        license="UNKNOWN — licence not stated",
        raw_metadata=json.dumps({
            "language": "ki",
            "title": "Gĩkũyũ oral history recording",
            "rights_state": "unknown_pending_rights_review",
            "collection_mode": "metadata_and_source_link_only",
        }),
    )
    ordinary_pending = Source(
        url="https://example.org/review",
        domain="example.org",
        source_type=SourceType.WEB,
        status=SourceStatus.PENDING,
        raw_metadata=json.dumps({
            "language": "ki",
            "title": "Needs review",
            "collection_mode": "full_text",
        }),
    )
    db_session.add_all([restricted, ordinary_pending])
    await db_session.commit()

    response = await client.get("/api/v1/sources/references")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["url"] == restricted.url
    assert body[0]["title"] == "Gĩkũyũ oral history recording"
    assert "body" not in body[0]
