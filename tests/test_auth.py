import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

BASE = "/api/v1/auth"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_register_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"email": "test_auth@example.com", "password": "secret123", "name": "Тест"}

        # register
        r = await client.post(f"{BASE}/register", json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # duplicate register → 409
        r2 = await client.post(f"{BASE}/register", json=payload)
        assert r2.status_code == 409

        # login
        r3 = await client.post(f"{BASE}/login", json={"email": payload["email"], "password": payload["password"]})
        assert r3.status_code == 200
        tokens = r3.json()

        # refresh
        r4 = await client.post(f"{BASE}/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert r4.status_code == 200

        # logout
        r5 = await client.post(f"{BASE}/logout", json={"refresh_token": tokens["refresh_token"]})
        assert r5.status_code == 204


@pytest.mark.anyio
async def test_login_wrong_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            f"{BASE}/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )
        assert r.status_code == 401


@pytest.mark.anyio
async def test_protected_without_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/users/me")
        assert r.status_code == 403  # HTTPBearer returns 403 when no credentials