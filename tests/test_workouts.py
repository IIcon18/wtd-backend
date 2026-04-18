import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

BASE_AUTH = "/api/v1/auth"
BASE_PROFILE = "/api/v1/swim-profile"
BASE_WORKOUTS = "/api/v1/workouts"


async def _get_token(client: AsyncClient, suffix: str = "") -> str:
    email = f"workout_user{suffix}@example.com"
    r = await client.post(
        f"{BASE_AUTH}/register",
        json={"email": email, "password": "pass1234", "name": "Тест"},
    )
    if r.status_code == 409:
        r = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": email, "password": "pass1234"},
        )
    return r.json()["access_token"]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_workouts_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(BASE_WORKOUTS + "/")
        assert r.status_code == 403


@pytest.mark.anyio
async def test_get_workouts_authenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_token(client, "_w1")
        r = await client.get(
            BASE_WORKOUTS + "/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_create_swim_profile():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _get_token(client, "_w2")
        headers = {"Authorization": f"Bearer {token}"}

        profile_data = {
            "level": "beginner",
            "goal": "endurance",
            "sessions_per_week": "3",
            "session_km": "1000",
            "pool_meters": "25",
        }
        r = await client.post(BASE_PROFILE + "/", json=profile_data, headers=headers)
        assert r.status_code in (201, 409), r.text

        r2 = await client.get(BASE_PROFILE + "/me", headers=headers)
        assert r2.status_code == 200
        data = r2.json()
        assert data["level"] == "beginner"
        assert data["goal"] == "endurance"