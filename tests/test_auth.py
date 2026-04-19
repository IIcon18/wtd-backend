"""Integration tests for /api/v1/auth endpoints."""
import pytest

BASE = "/api/v1/auth"


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_success(http_client):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    r = await http_client.post(f"{BASE}/register", json={
        "email": f"new_{suffix}@example.com",
        "password": "secret123",
        "name": "Новый",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_register_duplicate_email(http_client, registered_user):
    r = await http_client.post(f"{BASE}/register", json={
        "email": registered_user["email"],
        "password": "another123",
        "name": "Другой",
    })
    assert r.status_code == 409


@pytest.mark.anyio
async def test_register_missing_password(http_client):
    import uuid
    r = await http_client.post(f"{BASE}/register", json={
        "email": f"nopw_{uuid.uuid4().hex[:6]}@x.com",
        "name": "X",
    })
    assert r.status_code == 422


@pytest.mark.anyio
async def test_register_invalid_email(http_client):
    r = await http_client.post(f"{BASE}/register", json={
        "email": "not-an-email",
        "password": "pass123",
        "name": "X",
    })
    assert r.status_code == 422


@pytest.mark.anyio
async def test_register_missing_name(http_client):
    import uuid
    r = await http_client.post(f"{BASE}/register", json={
        "email": f"noname_{uuid.uuid4().hex[:6]}@x.com",
        "password": "pass123",
    })
    assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_login_success(http_client, registered_user):
    r = await http_client.post(f"{BASE}/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.anyio
async def test_login_wrong_password(http_client, registered_user):
    r = await http_client.post(f"{BASE}/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword",
    })
    assert r.status_code == 401


@pytest.mark.anyio
async def test_login_nonexistent_user(http_client):
    r = await http_client.post(f"{BASE}/login", json={
        "email": "nobody@example.com",
        "password": "anypassword",
    })
    assert r.status_code == 401


@pytest.mark.anyio
async def test_login_missing_fields(http_client):
    r = await http_client.post(f"{BASE}/login", json={"email": "only@email.com"})
    assert r.status_code == 422


# ── Refresh ───────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_refresh_success(http_client, registered_user):
    r = await http_client.post(f"{BASE}/refresh", json={
        "refresh_token": registered_user["refresh_token"],
    })
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()


@pytest.mark.anyio
async def test_refresh_invalid_token(http_client):
    r = await http_client.post(f"{BASE}/refresh", json={"refresh_token": "garbage"})
    assert r.status_code == 401


@pytest.mark.anyio
async def test_refresh_after_logout(http_client, registered_user):
    """Refresh token must be revoked after logout."""
    await http_client.post(f"{BASE}/logout", json={
        "refresh_token": registered_user["refresh_token"],
    })
    r = await http_client.post(f"{BASE}/refresh", json={
        "refresh_token": registered_user["refresh_token"],
    })
    assert r.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_logout_success(http_client, registered_user):
    r = await http_client.post(f"{BASE}/logout", json={
        "refresh_token": registered_user["refresh_token"],
    })
    assert r.status_code == 204


# ── Protected route guards ────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_protected_without_token(http_client):
    r = await http_client.get("/api/v1/users/me")
    assert r.status_code == 403


@pytest.mark.anyio
async def test_protected_with_invalid_token(http_client):
    r = await http_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert r.status_code == 401


@pytest.mark.anyio
async def test_protected_with_valid_token(http_client, auth_headers):
    r = await http_client.get("/api/v1/users/me", headers=auth_headers)
    assert r.status_code == 200
