from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.subscription import SubscriptionTier
from app.models.user import User
from app.repositories.subscription_repo import SubscriptionRepository
from app.schemas.subscription import SubscriptionOut

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=Optional[SubscriptionOut])
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SubscriptionRepository(db).get_active_subscription(current_user.id)


@router.post("/activate-test", response_model=SubscriptionOut)
async def activate_test_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Тестовая Pro-подписка на 7 дней — только для разработки."""
    now = datetime.now(timezone.utc)
    return await SubscriptionRepository(db).create_or_update(
        user_id=current_user.id,
        tier=SubscriptionTier.pro,
        started_at=now,
        expires_at=now + timedelta(days=7),
    )