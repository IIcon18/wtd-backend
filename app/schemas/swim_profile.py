from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.swim_profile import PoolSize, SessionKm, SessionsPerWeek, SwimGoal, SwimLevel


class SwimProfileCreate(BaseModel):
    level: SwimLevel
    goal: SwimGoal
    sessions_per_week: SessionsPerWeek
    session_km: SessionKm
    pool_meters: PoolSize


class SwimProfileUpdate(BaseModel):
    level: Optional[SwimLevel] = None
    goal: Optional[SwimGoal] = None
    sessions_per_week: Optional[SessionsPerWeek] = None
    session_km: Optional[SessionKm] = None
    pool_meters: Optional[PoolSize] = None


class SwimProfileOut(BaseModel):
    id: int
    user_id: int
    level: SwimLevel
    goal: SwimGoal
    sessions_per_week: SessionsPerWeek
    session_km: SessionKm
    pool_meters: PoolSize
    single_workout_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}