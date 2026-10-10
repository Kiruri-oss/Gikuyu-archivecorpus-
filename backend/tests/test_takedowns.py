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