"""Integration tests for /api/v1/swim-profile endpoints."""
import pytest

BASE = "/api/v1/swim-profile"

VALID_PROFILE = {
    "level": "beginner",
    "goal": "endurance",
    "sessions_per_week": "3",
    "session_km": "1000",
    "pool_meters": "25",
}


@pytest.mark.anyio
async def test_create_profile(http_client, auth_headers):
    r = await http_client.post(f"{BASE}/", json=VALID_PROFILE, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["level"] == "beginner"
    assert data["goal"] == "endurance"
    assert data["sessions_per_week"] == "3"
    assert data["pool_meters"] == "25"
    assert data["single_workout_available"] is False


@pytest.mark.anyio
async def test_create_profile_duplicate(http_client, auth_headers):
    await http_client.post(f"{BASE}/", json=VALID_PROFILE, headers=auth_headers)
    r = await http_client.post(f"{BASE}/", json=VALID_PROFILE, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.anyio
async def test_get_profile(http_client, auth_headers):
    await http_client.post(f"{BASE}/", json=VALID_PROFILE, headers=auth_headers)
    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["level"] == "beginner"
    assert data["goal"] == "endurance"


@pytest.mark.anyio
async def test_get_profile_not_found(http_client, auth_headers):
    """Fresh user has no profile yet."""
    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.anyio
async def test_update_profile(http_client, auth_headers):
    await http_client.post(f"{BASE}/", json=VALID_PROFILE, headers=auth_headers)
    r = await http_client.patch(f"{BASE}/me", json={"level": "advanced"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["level"] == "advanced"


@pytest.mark.anyio
async def test_update_goal(http_client, auth_headers):
    await http_client.post(f"{BASE}/", json=VALID_PROFILE, headers=auth_headers)
    r = await http_client.patch(
        f"{BASE}/me", json={"goal": "competition"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["goal"] == "competition"


@pytest.mark.anyio
async def test_profile_requires_auth_post(http_client):
    r = await http_client.post(f"{BASE}/", json=VALID_PROFILE)
    assert r.status_code == 401


@pytest.mark.anyio
async def test_profile_requires_auth_get(http_client):
    r = await http_client.get(f"{BASE}/me")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_invalid_level_value(http_client, auth_headers):
    bad = {**VALID_PROFILE, "level": "superhero"}
    r = await http_client.post(f"{BASE}/", json=bad, headers=auth_headers)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_invalid_pool_value(http_client, auth_headers):
    bad = {**VALID_PROFILE, "pool_meters": "33"}
    r = await http_client.post(f"{BASE}/", json=bad, headers=auth_headers)
    assert r.status_code == 422
