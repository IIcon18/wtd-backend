import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.swim_profile import SwimLevel
from app.models.workout import Workout, WorkoutType

logger = logging.getLogger(__name__)


class WorkoutRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, workout_id: int) -> Optional[Workout]:
        result = await self.db.execute(select(Workout).where(Workout.id == workout_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Workout]:
        result = await self.db.execute(select(Workout))
        return list(result.scalars().all())

    async def get_by_level(
        self,
        level: SwimLevel,
        limit: int = 3,
        exclude_type: Optional[WorkoutType] = None,
    ) -> List[Workout]:
        query = select(Workout).where(Workout.level == level)
        if exclude_type:
            query = query.where(Workout.type != exclude_type)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Workout:
        workout = Workout(**kwargs)
        self.db.add(workout)
        await self.db.commit()
        await self.db.refresh(workout)
        return workout