"""Integration tests for /api/v1/workouts endpoint."""
import pytest

BASE_AUTH = "/api/v1/auth"
BASE_PROFILE = "/api/v1/swim-profile"
BASE_WORKOUTS = "/api/v1/workouts"


@pytest.mark.anyio
async def test_get_workouts_requires_auth(http_client):
    r = await http_client.get(f"{BASE_WORKOUTS}/")
    assert r.status_code == 403


@pytest.mark.anyio
async def test_get_workouts_authenticated(http_client, auth_headers):
    r = await http_client.get(f"{BASE_WORKOUTS}/", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_get_workouts_response_structure(http_client, auth_headers):
    r = await http_client.get(f"{BASE_WORKOUTS}/", headers=auth_headers)
    assert r.status_code == 200
    workouts = r.json()
    if workouts:
        w = workouts[0]
        assert "id" in w
        assert "type" in w


@pytest.mark.anyio
async def test_create_swim_profile_and_get_workouts(http_client, auth_headers):
    """Creating a swim profile should not break workout listing."""
    await http_client.post(
        BASE_PROFILE + "/",
        json={
            "level": "beginner",
            "goal": "endurance",
            "sessions_per_week": "3",
            "session_km": "1000",
            "pool_meters": "25",
        },
        headers=auth_headers,
    )
    r = await http_client.get(f"{BASE_WORKOUTS}/", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
