"""Integration tests for /api/v1/admin endpoints — role-based access."""
import pytest

import app.core.database as _db
from app.models.payment import Payment, PaymentStatus, PaymentTier

BASE = "/api/v1/admin"


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _create_pending_payment(user_id: int, tier: str = "base", price: int = 299) -> int:
    """Insert a pending payment directly into the DB, return its id."""
    async with _db.AsyncSessionLocal() as db:
        payment = Payment(
            user_id=user_id,
            tier=PaymentTier(tier),
            price=price,
            status=PaymentStatus.pending,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment.id


async def _get_user_id(http_client, auth_headers: dict) -> int:
    r = await http_client.get("/api/v1/users/me", headers=auth_headers)
    return r.json()["id"]


# ── Access control ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_pending_requires_admin(http_client, auth_headers):
    r = await http_client.get(f"{BASE}/payments/", headers=auth_headers)
    assert r.status_code == 403


@pytest.mark.anyio
async def test_list_pending_unauthenticated(http_client):
    r = await http_client.get(f"{BASE}/payments/")
    assert r.status_code == 401


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
    user_id = await _get_user_id(http_client, auth_headers)
    payment_id = await _create_pending_payment(user_id, "base", 299)

    r = await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=admin_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "approved"
    assert data["processed_by"] is not None


@pytest.mark.anyio
async def test_decline_payment(http_client, admin_headers, auth_headers):
    user_id = await _get_user_id(http_client, auth_headers)
    payment_id = await _create_pending_payment(user_id, "pro", 599)

    r = await http_client.patch(
        f"{BASE}/payments/{payment_id}/decline", headers=admin_headers
    )
    assert r.status_code == 200
    assert r.json()["status"] == "declined"


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
    user_id = await _get_user_id(http_client, auth_headers)
    payment_id = await _create_pending_payment(user_id, "base", 299)

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
    user_id = await _get_user_id(http_client, auth_headers)
    payment_id = await _create_pending_payment(user_id, "single", 149)

    await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=admin_headers
    )

    r2 = await http_client.get("/api/v1/swim-profile/me", headers=auth_headers)
    assert r2.json()["single_workout_available"] is True


@pytest.mark.anyio
async def test_approve_requires_admin(http_client, auth_headers):
    """Regular user cannot approve payments."""
    user_id = await _get_user_id(http_client, auth_headers)
    payment_id = await _create_pending_payment(user_id, "base", 299)

    r = await http_client.patch(
        f"{BASE}/payments/{payment_id}/approve", headers=auth_headers
    )
    assert r.status_code == 403
