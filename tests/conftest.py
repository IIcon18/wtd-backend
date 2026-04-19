import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.user import User, UserRole

BASE_AUTH = "/api/v1/auth"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def http_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def registered_user(http_client):
    """Create a fresh user, return dict with email/password/tokens."""
    suffix = uuid.uuid4().hex[:8]
    email = f"user_{suffix}@test.com"
    password = "testpass123"
    r = await http_client.post(
        f"{BASE_AUTH}/register",
        json={"email": email, "password": password, "name": "Тест Юзер"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    return {
        "email": email,
        "password": password,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest.fixture
async def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
async def admin_user(http_client):
    """Create a user and promote to admin role directly in DB."""
    suffix = uuid.uuid4().hex[:8]
    email = f"admin_{suffix}@test.com"
    password = "adminpass123"
    r = await http_client.post(
        f"{BASE_AUTH}/register",
        json={"email": email, "password": password, "name": "Тест Админ"},
    )
    assert r.status_code == 201, r.text
    data = r.json()

    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User).where(User.email == email).values(role=UserRole.admin)
        )
        await db.commit()

    return {
        "email": email,
        "password": password,
        "access_token": data["access_token"],
    }


@pytest.fixture
async def admin_headers(admin_user):
    return {"Authorization": f"Bearer {admin_user['access_token']}"}
