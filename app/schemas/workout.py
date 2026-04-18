from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel

from app.models.swim_profile import SwimLevel
from app.models.workout import WorkoutType


class WorkoutOut(BaseModel):
    id: int
    level: SwimLevel
    type: WorkoutType
    duration_min: int
    pool_meters: int
    km_range: str
    content: Dict[str, Any]
    tags: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}