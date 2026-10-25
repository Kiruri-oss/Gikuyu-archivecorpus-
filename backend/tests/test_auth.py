import pytest

from app.core.security import create_access_token, create_refresh_token


@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "full_name": "Kamau Njoroge",
        "password": "StrongPass123!",
        "dialect": "Ki-Muranga",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_rejects_duplicate(client, contributor):
    resp = await client.post("/api/v1/auth/register", json={
        "email": contributor.email,
        "full_name": "Duplicate",
        "password": "StrongPass123!",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_returns_tokens(client, contributor):
    resp = await client.post("/api/v1/auth/login", json={
        "email": contributor.email,
        "password": "SecurePass123!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_rejects_bad_password(client, contributor):
    resp = await client.post("/api/v1/auth/login", json={
        "email": contributor.email,
        "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_current_user_rejects_malformed_uuid_subject(client):
    token = create_access_token("not-a-uuid", "contributor")
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token subject"


@pytest.mark.asyncio
async def test_refresh_token_uses_uuid_subject(client, contributor):
    token = create_refresh_token(str(contributor.id))
    response = await client.post("/api/v1/auth/refresh", params={"refresh_token": token})
    assert response.status_code == 200
    assert "access_token" in response.json()
