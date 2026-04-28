"""Integration tests for /api/v1/history endpoints."""
import uuid

import pytest

BASE = "/api/v1/history"

_SESSION = {
    "workout_type": "endurance",
    "duration_min": 45,
    "distance_m": 1500,
    "content": "Тренировка на выносливость",
}


@pytest.mark.anyio
async def test_get_history_empty(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_save_session(http_client, auth_headers):
    r = await http_client.post(f"{BASE}/save", json=_SESSION, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["workout_type"] == "endurance"
    assert data["duration_min"] == 45
    assert data["distance_m"] == 1500
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_save_then_list(http_client, auth_headers):
    await http_client.post(f"{BASE}/save", json=_SESSION, headers=auth_headers)
    r = await http_client.get(f"{BASE}/", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.anyio
async def test_get_session_by_id(http_client, auth_headers):
    r = await http_client.post(f"{BASE}/save", json=_SESSION, headers=auth_headers)
    session_id = r.json()["id"]

    r2 = await http_client.get(f"{BASE}/{session_id}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == session_id
    assert r2.json()["workout_type"] == "endurance"


@pytest.mark.anyio
async def test_get_session_not_found(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/999999", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.anyio
async def test_get_session_wrong_user_gets_403(http_client, auth_headers):
    """A session must only be accessible by its owner."""
    r = await http_client.post(f"{BASE}/save", json=_SESSION, headers=auth_headers)
    session_id = r.json()["id"]

    suffix = uuid.uuid4().hex[:8]
    r2 = await http_client.post(
        "/api/v1/auth/register",
        json={"email": f"intruder_{suffix}@test.com", "password": "pass1234", "name": "X"},
    )
    intruder_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    r3 = await http_client.get(f"{BASE}/{session_id}", headers=intruder_headers)
    assert r3.status_code == 403


@pytest.mark.anyio
async def test_history_requires_auth(http_client):
    r = await http_client.get(f"{BASE}/")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_save_requires_auth(http_client):
    r = await http_client.post(f"{BASE}/save", json=_SESSION)
    assert r.status_code == 401


@pytest.mark.anyio
async def test_save_missing_fields(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/save", json={"workout_type": "endurance"}, headers=auth_headers
    )
    assert r.status_code == 422
