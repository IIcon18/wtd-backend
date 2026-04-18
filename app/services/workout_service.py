import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.swim_profile import SwimLevel
from app.models.workout import Workout, WorkoutType
from app.repositories.workout_repo import WorkoutRepository

logger = logging.getLogger(__name__)


class WorkoutService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = WorkoutRepository(db)

    async def get_templates(
        self,
        level: SwimLevel,
        limit: int = 3,
        exclude_type: Optional[WorkoutType] = None,
    ) -> List[Workout]:
        return await self.repo.get_by_level(level, limit=limit, exclude_type=exclude_type)

    async def get_all(self) -> List[Workout]:
        return await self.repo.get_all()