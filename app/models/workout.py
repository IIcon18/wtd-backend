import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.swim_profile import SwimLevel


class WorkoutType(str, enum.Enum):
    technique = "technique"
    endurance = "endurance"
    speed = "speed"
    recovery = "recovery"


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[SwimLevel] = mapped_column(
        Enum(SwimLevel, name="swimlevel"), nullable=False
    )
    type: Mapped[WorkoutType] = mapped_column(
        Enum(WorkoutType, name="workouttype"), nullable=False
    )
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    pool_meters: Mapped[int] = mapped_column(Integer, nullable=False)
    km_range: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tags: Mapped[list] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )