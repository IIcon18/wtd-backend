"""Payment endpoints — YooKassa integration."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.payment import PaymentStatus, PaymentTier
from app.models.subscription import Subscription, SubscriptionTier
from app.models.user import User
from app.repositories.payment_repo import PaymentRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.swim_profile_repo import SwimProfileRepository
from app.schemas.payment import PaymentOut
from app.services.yookassa_service import (
    check_payment_succeeded,
    create_yookassa_payment,
    get_tier_price,
    parse_webhook,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


# ── Request / Response schemas ────────────────────────────────────────────────

class PaymentCreateRequest(BaseModel):
    tier: PaymentTier


class PaymentCreateResponse(BaseModel):
    payment_id: int
    confirmation_url: str
    price: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/create", response_model=PaymentCreateResponse, status_code=201)
async def create_payment(
    data: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a YooKassa payment and return the redirect URL."""
    tier_str = data.tier.value
    price = get_tier_price(tier_str)

    try:
        yk = create_yookassa_payment(tier_str, current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("YooKassa error: %s", exc)
        raise HTTPException(status_code=502, detail="Ошибка платёжной системы")

    payment = await PaymentRepository(db).create(
        user_id=current_user.id,
        tier=data.tier,
        price=price,
        yookassa_payment_id=yk["yookassa_id"],
    )

    return PaymentCreateResponse(
        payment_id=payment.id,
        confirmation_url=yk["confirmation_url"],
        price=price,
    )


@router.post("/webhook", include_in_schema=False)
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    YooKassa sends a POST here when a payment succeeds.
    No auth required — we validate via the SDK's signature check.
    """
    body = await request.body()

    try:
        result = parse_webhook(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if result is None:
        # Non-succeeded event — acknowledge and ignore
        return {"status": "ok"}

    yookassa_id, user_id_str, tier_str = result
    user_id = int(user_id_str)

    repo = PaymentRepository(db)
    payment = await repo.get_by_yookassa_id(yookassa_id)

    if payment is None:
        logger.error("Webhook for unknown yookassa_id=%s", yookassa_id)
        return {"status": "ok"}

    if payment.status == PaymentStatus.approved:
        logger.info("Duplicate webhook for payment id=%s — skipping", payment.id)
        return {"status": "ok"}

    # Mark payment approved
    payment.status = PaymentStatus.approved
    payment.updated_at = datetime.now(timezone.utc)

    if tier_str == PaymentTier.single.value:
        profile = await SwimProfileRepository(db).get_by_user_id(user_id)
        if profile:
            profile.single_workout_available = True
            logger.info("Granted single workout to user_id=%s", user_id)
    else:
        tier = SubscriptionTier(tier_str)
        now = datetime.now(timezone.utc)

        # Deactivate existing active subscriptions
        result_subs = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
        for sub in result_subs.scalars().all():
            sub.is_active = False

        db.add(
            Subscription(
                user_id=user_id,
                tier=tier,
                started_at=now,
                expires_at=now + timedelta(days=30),
                is_active=True,
            )
        )
        logger.info("Activated %s subscription for user_id=%s", tier_str, user_id)

    await db.commit()
    return {"status": "ok"}


class ConfirmResponse(BaseModel):
    status: str  # "activated" | "already_active" | "pending" | "failed"


@router.post("/{payment_id}/confirm", response_model=ConfirmResponse)
async def confirm_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the frontend after returning from YooKassa.
    Checks payment status directly via YooKassa API and activates
    the subscription if succeeded — no webhook needed.
    """
    repo = PaymentRepository(db)
    payment = await repo.get_by_id(payment_id)

    if not payment or payment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    if payment.status == PaymentStatus.approved:
        logger.info("Payment id=%s already activated", payment_id)
        return ConfirmResponse(status="already_active")

    if not payment.yookassa_payment_id:
        raise HTTPException(status_code=400, detail="Нет ID платежа ЮКасса")

    try:
        succeeded = check_payment_succeeded(payment.yookassa_payment_id)
    except Exception as exc:
        logger.error("YooKassa check failed for payment id=%s: %s", payment_id, exc)
        raise HTTPException(status_code=502, detail="Ошибка проверки платежа")

    if not succeeded:
        return ConfirmResponse(status="pending")

    # Activate subscription / single workout
    tier_str = payment.tier.value
    user_id = current_user.id
    now = datetime.now(timezone.utc)

    payment.status = PaymentStatus.approved
    payment.updated_at = now

    if tier_str == PaymentTier.single.value:
        profile = await SwimProfileRepository(db).get_by_user_id(user_id)
        if profile:
            profile.single_workout_available = True
            logger.info("Granted single workout to user_id=%s", user_id)
    else:
        tier = SubscriptionTier(tier_str)
        result_subs = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
        for sub in result_subs.scalars().all():
            sub.is_active = False

        db.add(Subscription(
            user_id=user_id,
            tier=tier,
            started_at=now,
            expires_at=now + timedelta(days=30),
            is_active=True,
        ))
        logger.info("Activated %s subscription for user_id=%s", tier_str, user_id)

    await db.commit()
    return ConfirmResponse(status="activated")


@router.get("/me", response_model=List[PaymentOut])
async def get_my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentRepository(db).get_by_user_id(current_user.id)
