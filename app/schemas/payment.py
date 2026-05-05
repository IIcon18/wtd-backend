from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.payment import PaymentStatus, PaymentTier


class PaymentCreate(BaseModel):
    tier: PaymentTier
    price: int
    screenshot_file_id: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    user_id: int
    tier: PaymentTier
    price: int
    screenshot_file_id: Optional[str]
    yookassa_payment_id: Optional[str]
    status: PaymentStatus
    processed_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}