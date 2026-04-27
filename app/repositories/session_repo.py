import logging
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession
from app.models.workout import WorkoutType

logger = logging.getLogger(__name__)


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, session_id: int) -> Optional[UserSession]:
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, user_id: int, limit: int = 20, skip: int = 0
    ) -> List[UserSession]:
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(desc(UserSession.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, user_id: int, limit: int = 5) -> List[UserSession]:
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(desc(UserSession.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        workout_type: WorkoutType,
        duration_min: int,
        distance_m: int,
        content: str,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            workout_type=workout_type,
            duration_min=duration_min,
            distance_m=distance_m,
            content=content,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info("Saved session id=%s for user_id=%s", session.id, user_id)
        return session

    async def count_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(UserSession.id)).where(UserSession.user_id == user_id)
        )
        return result.scalar_one()