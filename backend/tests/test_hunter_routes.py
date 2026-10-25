import pytest


@pytest.mark.asyncio
async def test_hunter_controls_require_admin_authentication(client):
    status_response = await client.get("/api/v1/hunter/status")
    run_response = await client.post("/api/v1/hunter/run?max_pages=1")

    assert status_response.status_code == 401
    assert run_response.status_code == 401
