import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.swim_profile import SwimProfile

logger = logging.getLogger(__name__)


class SwimProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[SwimProfile]:
        result = await self.db.execute(
            select(SwimProfile).where(SwimProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, **kwargs) -> SwimProfile:
        profile = SwimProfile(user_id=user_id, **kwargs)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info("Created swim profile for user_id=%s", user_id)
        return profile

    async def update(self, profile: SwimProfile, **kwargs) -> SwimProfile:
        for key, value in kwargs.items():
            setattr(profile, key, value)
        profile.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile