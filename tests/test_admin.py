"""Integration tests for /api/v1/admin endpoints — role-based access."""
import pytest

BASE = "/api/v1/admin"
PAYMENTS_BASE = "/api/v1/payments"


# ── Access control ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_pending_requires_admin(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/payments/", headers=auth_headers)
    assert r.status_code == 403


@pytest.mark.anyio
async def test_list_pending_unauthenticated(http_client):
    r = await http_client.get(f"{BASE}/payments/")
    assert r.status_code == 403


@pytest.mark.anyio
async def test_list_users_requires_admin(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/users/", headers=auth_headers)
    assert r.status_code == 403


@pytest.mark.anyio
async def test_stats_requires_admin(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/stats/", headers=auth_headers)
    assert r.status_code == 403


# ── Admin happy paths ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_pending_payments_admin(http_client, admin_headers):
    r = await http_client.get(f"{BASE}/payments/", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_list_users_admin(http_client, admin_headers):
    r = await http_client.get(f"{BASE}/users/", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


@pytest.mark.anyio
async def test_get_stats_admin(http_client, admin_headers):
    r = await http_client.get(f"{BASE}/stats/", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_users" in data
    assert "pending_payments" in data
    assert "approved_payments" in data
    assert "total_revenue" in data


# ── Approve / decline ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_approve_payment(http_client, admin_headers, auth_headers):
    r = await http_client.post(
        f"{PAYMENTS_BASE}/", json={"tier": "base", "price": 499}, headers=auth_headers
    )
    payment_id = r.json()["id"]

    r2 = await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=admin_headers
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "approved"
    assert data["processed_by"] is not None


@pytest.mark.anyio
async def test_decline_payment(http_client, admin_headers, auth_headers):
    r = await http_client.post(
        f"{PAYMENTS_BASE}/", json={"tier": "pro", "price": 999}, headers=auth_headers
    )
    payment_id = r.json()["id"]

    r2 = await http_client.patch(
        f"{BASE}/payments/{payment_id}/decline", headers=admin_headers
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "declined"


@pytest.mark.anyio
async def test_approve_nonexistent_payment(http_client, admin_headers):
    r = await http_client.patch(
        f"{BASE}/payments/999999/approve", headers=admin_headers
    )
    assert r.status_code == 404


@pytest.mark.anyio
async def test_decline_nonexistent_payment(http_client, admin_headers):
    r = await http_client.patch(
        f"{BASE}/payments/999999/decline", headers=admin_headers
    )
    assert r.status_code == 404


@pytest.mark.anyio
async def test_approve_grants_subscription(http_client, admin_headers, auth_headers):
    """Approving a 'base' payment must create an active subscription for the user."""
    r = await http_client.post(
        f"{PAYMENTS_BASE}/", json={"tier": "base", "price": 499}, headers=auth_headers
    )
    payment_id = r.json()["id"]
    await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=admin_headers
    )

    r2 = await http_client.get("/api/v1/subscriptions/me", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["tier"] == "base"
    assert r2.json()["is_active"] is True


@pytest.mark.anyio
async def test_approve_single_grants_single_workout(http_client, admin_headers, auth_headers):
    """Approving a 'single' payment must set single_workout_available=True on the swim profile."""
    await http_client.post(
        "/api/v1/swim-profile/",
        json={
            "level": "beginner",
            "goal": "endurance",
            "sessions_per_week": "3",
            "session_km": "1000",
            "pool_meters": "25",
        },
        headers=auth_headers,
    )
    r = await http_client.post(
        f"{PAYMENTS_BASE}/", json={"tier": "single", "price": 199}, headers=auth_headers
    )
    payment_id = r.json()["id"]
    await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=admin_headers
    )

    r2 = await http_client.get("/api/v1/swim-profile/me", headers=auth_headers)
    assert r2.json()["single_workout_available"] is True


@pytest.mark.anyio
async def test_approve_requires_admin(http_client, auth_headers):
    """Regular user cannot approve payments."""
    r = await http_client.post(
        f"{PAYMENTS_BASE}/", json={"tier": "base", "price": 499}, headers=auth_headers
    )
    payment_id = r.json()["id"]
    r2 = await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=auth_headers
    )
    assert r2.status_code == 403
