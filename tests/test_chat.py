import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

BASE_AUTH = "/api/v1/auth"
BASE_CHAT = "/api/v1/chat"
BASE_PROFILE = "/api/v1/swim-profile"


async def _register_with_profile(client: AsyncClient, suffix: str) -> str:
    email = f"chat_user{suffix}@example.com"
    r = await client.post(
        f"{BASE_AUTH}/register",
        json={"email": email, "password": "pass1234", "name": "Чат"},
    )
    if r.status_code == 409:
        r = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": email, "password": "pass1234"},
        )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        f"{BASE_PROFILE}/",
        json={
            "level": "beginner",
            "goal": "endurance",
            "sessions_per_week": "3",
            "session_km": "1000",
            "pool_meters": "25",
        },
        headers=headers,
    )
    return token


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_chat_requires_subscription():
    """Without subscription chat returns 403."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_with_profile(client, "_c1")
        r = await client.post(
            f"{BASE_CHAT}/message",
            json={"message": "Привет, тренер!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403
        assert "подписка" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_chat_history_authenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_with_profile(client, "_c2")
        r = await client.get(
            f"{BASE_CHAT}/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)