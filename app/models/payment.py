import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PaymentTier(str, enum.Enum):
    single = "single"
    base = "base"
    pro = "pro"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    declined = "declined"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[PaymentTier] = mapped_column(
        Enum(PaymentTier, name="paymenttier"), nullable=False
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    screenshot_file_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="paymentstatus"),
        nullable=False,
        server_default="pending",
    )
    processed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        back_populates="payments", foreign_keys=[user_id]
    )
    admin: Mapped[Optional["User"]] = relationship(foreign_keys=[processed_by])