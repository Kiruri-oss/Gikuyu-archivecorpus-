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


@pytest.mark.asyncio
async def test_member_contribution_summary_is_private_and_reports_review_state(client, db_session, contributor):
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.text_record import TextRecord
    from app.models.user import User, UserRole
    from app.core.security import hash_password, create_access_token

    other_user = User(
        email="another-contributor@example.com",
        full_name="Another Contributor",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.CONTRIBUTOR,
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()

    for suffix, owner in (("mine", contributor), ("theirs", other_user)):
        source = Source(
            url=f"test://member-summary/{suffix}",
            domain="test",
            source_type=SourceType.USER_UPLOAD,
            status=SourceStatus.PENDING,
        )
        db_session.add(source)
        await db_session.flush()
        db_session.add(TextRecord(
            source_id=source.id,
            contributor_id=owner.id,
            title=f"{suffix} proverb",
            body="Nĩ wega, andũ a Gĩkũyũ.",
            language_code="ki",
            sha256=uuid.uuid4().hex,
            license="CC0",
            allow_public_display=False,
            allow_research_use=False,
            allow_ai_training=False,
            allow_commercial_use=False,
        ))
    await db_session.commit()

    own_token = create_access_token(str(contributor.id), contributor.role.value)
    response = await client.get("/api/v1/community/me", headers={"Authorization": f"Bearer {own_token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"]["total"] == 1
    assert payload["totals"]["texts"] == 1
    assert payload["totals"]["pending"] == 1
    assert payload["totals"]["approved"] == 0
    assert [item["title"] for item in payload["recent"]] == ["mine proverb"]
    assert "another-contributor@example.com" not in str(payload)


@pytest.mark.asyncio
async def test_saved_references_are_owned_and_idempotent(client, auth_headers):
    payload = {
        "reference_key": "reference-123",
        "title": "Gĩkũyũ language resource",
        "source_name": "Example archive",
        "source_url": "https://example.org/gikuyu-resource",
    }
    first = await client.post("/api/v1/community/saved-references", json=payload, headers=auth_headers)
    assert first.status_code == 201
    saved_id = first.json()["id"]

    updated = {**payload, "title": "Updated Gĩkũyũ resource title"}
    second = await client.post("/api/v1/community/saved-references", json=updated, headers=auth_headers)
    assert second.status_code == 201
    assert second.json()["id"] == saved_id
    assert second.json()["title"] == "Updated Gĩkũyũ resource title"

    listing = await client.get("/api/v1/community/saved-references", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 1
    assert listing.json()["items"][0]["reference_key"] == "reference-123"

    removed = await client.delete(f"/api/v1/community/saved-references/{saved_id}", headers=auth_headers)
    assert removed.status_code == 204
    listing_after_delete = await client.get("/api/v1/community/saved-references", headers=auth_headers)
    assert listing_after_delete.status_code == 200
    assert listing_after_delete.json()["items"] == []


@pytest.mark.asyncio
async def test_saved_references_require_sign_in(client):
    payload = {
        "reference_key": "reference-anonymous",
        "title": "Gĩkũyũ resource",
        "source_name": "Example archive",
        "source_url": "https://example.org/gikuyu",
    }
    response = await client.post("/api/v1/community/saved-references", json=payload)
    assert response.status_code == 401
