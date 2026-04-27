import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionTier

logger = logging.getLogger(__name__)


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.expires_at > now,
            )
            .order_by(Subscription.expires_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> List[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.expires_at.desc())
        )
        return list(result.scalars().all())

    async def create_or_update(
        self,
        user_id: int,
        tier: SubscriptionTier,
        started_at: datetime,
        expires_at: datetime,
    ) -> Subscription:
        # deactivate existing active subscriptions
        existing = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
            )
        )
        for sub in existing.scalars().all():
            sub.is_active = False

        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            started_at=started_at,
            expires_at=expires_at,
            is_active=True,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        logger.info("Created subscription tier=%s for user_id=%s", tier, user_id)
        return subscription

    async def increment_ai_requests(self, subscription: Subscription) -> Subscription:
        subscription.ai_requests_today += 1
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription