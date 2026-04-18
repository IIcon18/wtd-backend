from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.workout_repo import WorkoutRepository
from app.schemas.workout import WorkoutOut

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=List[WorkoutOut])
async def get_workouts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkoutRepository(db).get_all()