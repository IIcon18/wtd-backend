import logging
from datetime import date

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    from app.repositories.user_repo import UserRepository

    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user_id = int(payload["sub"])
    user = await UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.admin:
        raise ForbiddenError("Admin access required")
    return current_user


async def check_chat_access(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Verify the user has chat access based on subscription or single workout."""
    from app.repositories.subscription_repo import SubscriptionRepository
    from app.repositories.swim_profile_repo import SwimProfileRepository

    profile_repo = SwimProfileRepository(db)
    sub_repo = SubscriptionRepository(db)

    profile = await profile_repo.get_by_user_id(current_user.id)

    if profile and profile.single_workout_available:
        return current_user

    subscription = await sub_repo.get_active_subscription(current_user.id)

    if not subscription:
        raise ForbiddenError("Нужна подписка")

    if subscription.tier.value == "pro":
        return current_user

    # base: 3 requests per day — atomic Redis counter prevents race conditions
    today = date.today().isoformat()
    key = f"ai_limit:{current_user.id}:{today}"
    redis = await get_redis()

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 90000)  # ~25 h — covers the full day with margin

    if count > 3:
        await redis.decr(key)
        raise ForbiddenError("Превышен лимит запросов на сегодня (3/3)")

    return current_user