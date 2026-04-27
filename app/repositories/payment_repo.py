import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus, PaymentTier

logger = logging.getLogger(__name__)


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> List[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_pending(self) -> List[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.status == PaymentStatus.pending)
        )
        return list(result.scalars().all())

    async def get_all(self) -> List[Payment]:
        result = await self.db.execute(select(Payment))
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        tier: PaymentTier,
        price: int,
        screenshot_file_id: Optional[str] = None,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            tier=tier,
            price=price,
            screenshot_file_id=screenshot_file_id,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        logger.info("Created payment id=%s tier=%s user_id=%s", payment.id, tier, user_id)
        return payment

    async def update_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        processed_by: Optional[int] = None,
    ) -> Payment:
        payment.status = status
        payment.updated_at = datetime.now(timezone.utc)
        if processed_by is not None:
            payment.processed_by = processed_by
        await self.db.commit()
        await self.db.refresh(payment)
        logger.info("Payment id=%s -> status=%s", payment.id, status)
        return payment