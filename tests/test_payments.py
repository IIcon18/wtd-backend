"""Integration tests for /api/v1/payments endpoints."""
import pytest

BASE = "/api/v1/payments"


@pytest.mark.anyio
async def test_create_payment_base_tier(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/", json={"tier": "base", "price": 499}, headers=auth_headers
    )
    assert r.status_code == 201
    data = r.json()
    assert data["tier"] == "base"
    assert data["status"] == "pending"
    assert data["price"] == 499
    assert data["processed_by"] is None


@pytest.mark.anyio
async def test_create_payment_pro_tier(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/", json={"tier": "pro", "price": 999}, headers=auth_headers
    )
    assert r.status_code == 201
    assert r.json()["tier"] == "pro"


@pytest.mark.anyio
async def test_create_payment_single_tier(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/", json={"tier": "single", "price": 199}, headers=auth_headers
    )
    assert r.status_code == 201
    assert r.json()["tier"] == "single"


@pytest.mark.anyio
async def test_create_payment_with_screenshot(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/",
        json={"tier": "base", "price": 499, "screenshot_file_id": "file_abc123"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["screenshot_file_id"] == "file_abc123"


@pytest.mark.anyio
async def test_get_my_payments_empty(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_get_my_payments_after_create(http_client, auth_headers):
    await http_client.post(
        f"{BASE}/", json={"tier": "base", "price": 499}, headers=auth_headers
    )
    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    assert r.status_code == 200
    payments = r.json()
    assert len(payments) >= 1
    assert payments[0]["tier"] == "base"


@pytest.mark.anyio
async def test_payments_only_own(http_client, auth_headers):
    """User sees only their own payments."""
    import uuid
    suffix = uuid.uuid4().hex[:8]
    r2 = await http_client.post(
        "/api/v1/auth/register",
        json={"email": f"other_{suffix}@test.com", "password": "pass1234", "name": "Other"},
    )
    other_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    await http_client.post(
        f"{BASE}/", json={"tier": "pro", "price": 999}, headers=other_headers
    )

    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    for p in r.json():
        assert p["user_id"] != r2.json().get("id", -1)


@pytest.mark.anyio
async def test_create_payment_invalid_tier(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/", json={"tier": "gold", "price": 100}, headers=auth_headers
    )
    assert r.status_code == 422


@pytest.mark.anyio
async def test_payments_requires_auth(http_client):
    r = await http_client.get(f"{BASE}/me")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_create_payment_requires_auth(http_client):
    r = await http_client.post(f"{BASE}/", json={"tier": "base", "price": 499})
    assert r.status_code == 401
