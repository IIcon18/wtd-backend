import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.exceptions import NotFoundError
from app.models.payment import PaymentStatus, PaymentTier
from app.models.subscription import Subscription, SubscriptionTier
from app.models.user import User
from app.repositories.payment_repo import PaymentRepository
from app.repositories.swim_profile_repo import SwimProfileRepository
from app.repositories.user_repo import UserRepository
from app.schemas.payment import PaymentOut
from app.schemas.user import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/payments/", response_model=List[PaymentOut])
async def list_pending_payments(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentRepository(db).get_pending()


@router.patch("/payments/{payment_id}/approve", response_model=PaymentOut)
async def approve_payment(
    payment_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    payment = await PaymentRepository(db).get_by_id(payment_id)
    if not payment:
        raise NotFoundError("Платёж не найден")

    # Stage all side-effects before the single commit so they're atomic.
    payment.status = PaymentStatus.approved
    payment.processed_by = admin.id
    payment.updated_at = datetime.now(timezone.utc)

    if payment.tier == PaymentTier.single:
        profile = await SwimProfileRepository(db).get_by_user_id(payment.user_id)
        if profile:
            profile.single_workout_available = True
            logger.info("Granted single workout to user_id=%s", payment.user_id)
    else:
        tier = SubscriptionTier(payment.tier.value)
        now = datetime.now(timezone.utc)

        # Deactivate existing active subscriptions
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == payment.user_id,
                Subscription.is_active.is_(True),
            )
        )
        for sub in result.scalars().all():
            sub.is_active = False

        db.add(Subscription(
            user_id=payment.user_id,
            tier=tier,
            started_at=now,
            expires_at=now + timedelta(days=30),
            is_active=True,
        ))

    await db.commit()
    await db.refresh(payment)
    logger.info("Payment id=%s approved by admin_id=%s", payment.id, admin.id)
    return payment


@router.patch("/payments/{payment_id}/decline", response_model=PaymentOut)
async def decline_payment(
    payment_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(db)
    payment = await repo.get_by_id(payment_id)
    if not payment:
        raise NotFoundError("Платёж не найден")
    return await repo.update_status(
        payment, PaymentStatus.declined, processed_by=admin.id
    )


@router.get("/users/", response_model=List[UserOut])
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await UserRepository(db).get_all()


@router.get("/stats/", response_model=Dict[str, Any])
async def get_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    payment_repo = PaymentRepository(db)

    total_users = await user_repo.count()
    pending = await payment_repo.get_pending()
    all_payments = await payment_repo.get_all()

    approved = [p for p in all_payments if p.status == PaymentStatus.approved]
    total_revenue = sum(p.price for p in approved)

    return {
        "total_users": total_users,
        "pending_payments": len(pending),
        "approved_payments": len(approved),
        "total_revenue": total_revenue,
    }