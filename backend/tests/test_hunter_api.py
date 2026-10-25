from unittest.mock import AsyncMock

import pytest

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_hunter_controls_require_admin(client):
    status_response = await client.get("/api/v1/hunter/status")
    run_response = await client.post("/api/v1/hunter/run")

    assert status_response.status_code == 401
    assert run_response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_check_hunter_status_and_start_bounded_run(
    client, db_session, monkeypatch
):
    admin = User(
        email="hunter-admin@example.com",
        full_name="Hunter Admin",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    headers = {
        "Authorization": "Bearer " + create_access_token(str(admin.id), UserRole.ADMIN.value)
    }
    status_response = await client.get("/api/v1/hunter/status", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["seed_count"] > 0
    assert status_response.json()["max_pages_per_run"] == 1000

    fake_run = AsyncMock(return_value={
        "status": "completed",
        "max_pages": 17,
        "found": 8,
        "saved": 5,
    })
    monkeypatch.setattr("app.api.v1.hunter.crawl_scheduler.run_web_crawl", fake_run)
    run_response = await client.post(
        "/api/v1/hunter/run?max_pages=17",
        headers=headers,
    )

    assert run_response.status_code == 200
    assert run_response.json()["saved"] == 5
    fake_run.assert_awaited_once_with(max_pages=17)
