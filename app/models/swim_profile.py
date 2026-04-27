import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class SwimLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class SwimGoal(str, enum.Enum):
    weight_loss = "weight_loss"
    endurance = "endurance"
    technique = "technique"
    competition = "competition"


class SessionsPerWeek(str, enum.Enum):
    two = "2"
    three = "3"
    five = "5"


class SessionKm(str, enum.Enum):
    km_1000 = "1000"
    km_1500 = "1500"
    km_2000 = "2000"
    km_2500_plus = "2500+"


class PoolSize(str, enum.Enum):
    m_25 = "25"
    m_50 = "50"


class SwimProfile(Base):
    __tablename__ = "swim_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    level: Mapped[SwimLevel] = mapped_column(
        Enum(SwimLevel, name="swimlevel"), nullable=False
    )
    goal: Mapped[SwimGoal] = mapped_column(
        Enum(SwimGoal, name="swimgoal"), nullable=False
    )
    sessions_per_week: Mapped[SessionsPerWeek] = mapped_column(
        Enum(SessionsPerWeek, name="sessionsperweek",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    session_km: Mapped[SessionKm] = mapped_column(
        Enum(SessionKm, name="sessionkm",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    pool_meters: Mapped[PoolSize] = mapped_column(
        Enum(PoolSize, name="poolsize",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    single_workout_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="swim_profile")