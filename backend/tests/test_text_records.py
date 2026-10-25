import pytest


@pytest.mark.asyncio
async def test_text_submission_requires_rights_and_storage_consent(client, auth_headers):
    response = await client.post("/api/v1/text-records", json={
        "title": "Sample Gĩkũyũ story",
        "body": "Rũciinĩ rũrĩa...",
        "language_code": "ki",
        "license": "CC BY 4.0",
    }, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_text_submission_is_held_for_review_then_published(client, db_session, auth_headers, contributor):
    from app.models.source import Source, SourceStatus
    from app.models.user import User, UserRole
    from app.core.security import create_access_token

    reviewer = User(
        email="reviewer@example.com",
        full_name="Archive Reviewer",
        hashed_password="not-used-in-test",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    db_session.add(reviewer)
    await db_session.commit()
    reviewer_headers = {"Authorization": f"Bearer {create_access_token(str(reviewer.id), reviewer.role.value)}"}

    payload = {
        "title": "Sample Gĩkũyũ story",
        "body": "Rũciinĩ rũrĩa twathiĩire gĩthaka-inĩ.",
        "language_code": "ki",
        "dialect": "Ki-Murang'a",
        "genre": "oral story",
        "license": "CC BY 4.0",
        "allow_research_use": True,
        "allow_ai_training": False,
        "allow_commercial_use": False,
        "consent_to_archive": True,
        "confirm_rights": True,
    }
    submitted = await client.post("/api/v1/text-records", json=payload, headers=auth_headers)
    assert submitted.status_code == 201, submitted.text
    body = submitted.json()
    assert body["language_code"] == "ki"
    assert body["allow_ai_training"] is False

    public_before_review = await client.get("/api/v1/text-records")
    assert public_before_review.status_code == 200
    assert public_before_review.json() == []

    pending_sources = await client.get("/api/v1/sources?status_filter=pending", headers=reviewer_headers)
    assert pending_sources.status_code == 200
    assert len(pending_sources.json()) == 1
    source_id = pending_sources.json()[0]["id"]
    reviewed = await client.patch(
        f"/api/v1/sources/{source_id}/review",
        json={"status": "approved", "reviewer_notes": "Rights and language checked."},
        headers=reviewer_headers,
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "approved"

    public_after_review = await client.get("/api/v1/text-records?language_code=ki")
    assert public_after_review.status_code == 200
    assert len(public_after_review.json()) == 1
    assert public_after_review.json()[0]["title"] == payload["title"]


@pytest.mark.asyncio
async def test_text_submission_rejects_duplicate_content(client, auth_headers):
    payload = {
        "title": "Duplicate guard",
        "body": "Same exact text body for the archive.",
        "language_code": "ki",
        "license": "CC BY 4.0",
        "consent_to_archive": True,
        "confirm_rights": True,
    }
    first = await client.post("/api/v1/text-records", json=payload, headers=auth_headers)
    second = await client.post("/api/v1/text-records", json=payload, headers=auth_headers)
    assert first.status_code == 201, first.text
    assert second.status_code == 409
