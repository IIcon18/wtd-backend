from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
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