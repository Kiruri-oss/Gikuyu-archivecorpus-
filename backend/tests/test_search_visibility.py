import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord


@pytest.mark.asyncio
async def test_search_hides_takedown_and_non_gikuyu_text_from_stale_index(
    client, db_session
):
    approved_source = Source(
        url="https://example.org/gikuyu",
        domain="example.org",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
    )
    removed_source = Source(
        url="https://example.org/removed",
        domain="example.org",
        source_type=SourceType.WEB,
        status=SourceStatus.TAKEN_DOWN,
    )
    legacy_source = Source(
        url="https://example.org/legacy",
        domain="example.org",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
    )
    db_session.add_all([approved_source, removed_source, legacy_source])
    await db_session.flush()

    approved = TextRecord(
        source_id=approved_source.id,
        title="Gĩkũyũ text",
        body="Mũciĩ nĩ ũhoro.",
        language_code="ki",
        sha256=uuid.uuid4().hex,
        license="CC-BY",
        allow_public_display=True,
    )
    removed = TextRecord(
        source_id=removed_source.id,
        title="Removed text",
        body="Mũciĩ nĩ ũhoro wa andũ.",
        language_code="ki",
        sha256=uuid.uuid4().hex,
        license="CC-BY",
        allow_public_display=True,
    )
    legacy_non_gikuyu = TextRecord(
        source_id=legacy_source.id,
        title="Legacy non-Gĩkũyũ record",
        body="This record predates language-scope validation.",
        language_code="sw",
        sha256=uuid.uuid4().hex,
        license="CC-BY",
        allow_public_display=True,
    )
    db_session.add_all([approved, removed, legacy_non_gikuyu])
    await db_session.commit()

    async def fake_search(index, query, limit=20):
        if index != "texts":
            return {"hits": []}
        return {
            "hits": [
                {"id": str(approved.id), "title": approved.title},
                {"id": str(removed.id), "title": removed.title},
                {"id": str(legacy_non_gikuyu.id), "title": legacy_non_gikuyu.title},
                {"id": "not-in-database", "title": "Stale index document"},
            ]
        }

    with patch(
        "app.api.v1.search.search_index.search",
        new_callable=AsyncMock,
        side_effect=fake_search,
    ):
        response = await client.get("/api/v1/search?q=Gikuyu")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["texts"]] == [str(approved.id)]
