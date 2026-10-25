import uuid

import pytest


@pytest.mark.asyncio
async def test_leaderboard_counts_only_approved_public_gikuyu_text(client, db_session, contributor):
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.text_record import TextRecord

    source = Source(
        url="test://leaderboard-text",
        domain="test",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.APPROVED,
    )
    db_session.add(source)
    await db_session.flush()
    db_session.add(TextRecord(
        source_id=source.id,
        contributor_id=contributor.id,
        title="Approved proverb",
        body="Nĩ wega.",
        language_code="ki",
        sha256=uuid.uuid4().hex,
        license="CC0",
        allow_public_display=True,
        allow_research_use=True,
        allow_ai_training=True,
        allow_commercial_use=True,
    ))
    await db_session.commit()

    response = await client.get("/api/v1/community/leaderboard")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["rank"] == 1
    assert items[0]["approved_contributions"] == 1
    assert items[0]["texts"] == 1
    assert items[0]["recordings"] == 0
    assert items[0]["display_name"].startswith("Contributor ")
    assert contributor.email not in str(items)
