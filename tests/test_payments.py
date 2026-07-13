"""Integration tests for /api/v1/payments endpoints."""
import uuid
from unittest.mock import patch

import pytest

BASE = "/api/v1/payments"


def _mock_yk(price: int) -> dict:
    """Fresh yookassa_id per call — the DB has a unique constraint on it and
    tests share one database with no per-test transaction rollback."""
    return {
        "yookassa_id": f"yk_test_{uuid.uuid4().hex[:8]}",
        "confirmation_url": "https://yookassa.ru/checkout/test",
        "price": price,
    }


@pytest.mark.anyio
async def test_create_payment_base_tier(http_client, auth_headers):
    with patch("app.api.v1.payments.create_yookassa_payment", return_value=_mock_yk(299)):
        r = await http_client.post(
            f"{BASE}/create", json={"tier": "base"}, headers=auth_headers
        )
    assert r.status_code == 201
    data = r.json()
    assert "payment_id" in data
    assert "confirmation_url" in data
    assert data["price"] == 299


@pytest.mark.anyio
async def test_create_payment_pro_tier(http_client, auth_headers):
    with patch("app.api.v1.payments.create_yookassa_payment", return_value=_mock_yk(599)):
        r = await http_client.post(
            f"{BASE}/create", json={"tier": "pro"}, headers=auth_headers
        )
    assert r.status_code == 201
    assert r.json()["price"] == 599


@pytest.mark.anyio
async def test_create_payment_single_tier(http_client, auth_headers):
    with patch("app.api.v1.payments.create_yookassa_payment", return_value=_mock_yk(149)):
        r = await http_client.post(
            f"{BASE}/create", json={"tier": "single"}, headers=auth_headers
        )
    assert r.status_code == 201
    assert r.json()["price"] == 149


@pytest.mark.anyio
async def test_get_my_payments_empty(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_get_my_payments_after_create(http_client, auth_headers):
    with patch("app.api.v1.payments.create_yookassa_payment", return_value=_mock_yk(299)):
        await http_client.post(
            f"{BASE}/create", json={"tier": "base"}, headers=auth_headers
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
    with patch("app.api.v1.payments.create_yookassa_payment", return_value=_mock_yk(599)):
        await http_client.post(
            f"{BASE}/create", json={"tier": "pro"}, headers=other_headers
        )

    r = await http_client.get(f"{BASE}/me", headers=auth_headers)
    for p in r.json():
        assert p["user_id"] != r2.json().get("id", -1)


@pytest.mark.anyio
async def test_create_payment_invalid_tier(http_client, auth_headers):
    r = await http_client.post(
        f"{BASE}/create", json={"tier": "gold"}, headers=auth_headers
    )
    assert r.status_code == 422


@pytest.mark.anyio
async def test_payments_requires_auth(http_client):
    r = await http_client.get(f"{BASE}/me")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_create_payment_requires_auth(http_client):
    r = await http_client.post(f"{BASE}/create", json={"tier": "base"})
    assert r.status_code == 401
