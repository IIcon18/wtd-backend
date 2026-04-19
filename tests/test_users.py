"""Integration tests for /api/v1/users endpoints."""
import pytest

BASE = "/api/v1/users"


@pytest.mark.anyio
async def test_get_me(http_client, registered_user, auth_headers):
    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == registered_user["email"]
    assert "id" in data
    assert "name" in data
    assert "role" in data
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_get_me_unauthenticated(http_client):
    r = await http_client.get(f"{BASE}/me")
    assert r.status_code == 403


@pytest.mark.anyio
async def test_get_me_bad_token(http_client):
    r = await http_client.get(f"{BASE}/me", headers={"Authorization": "Bearer bad"})
    assert r.status_code == 401


@pytest.mark.anyio
async def test_update_name(http_client, auth_headers):
    r = await http_client.patch(f"{BASE}/me", json={"name": "Новое Имя"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Новое Имя"


@pytest.mark.anyio
async def test_update_empty_body(http_client, auth_headers):
    """PATCH with no fields is valid — returns current user unchanged."""
    r = await http_client.patch(f"{BASE}/me", json={}, headers=auth_headers)
    assert r.status_code == 200
    assert "email" in r.json()


@pytest.mark.anyio
async def test_update_me_unauthenticated(http_client):
    r = await http_client.patch(f"{BASE}/me", json={"name": "X"})
    assert r.status_code == 403
