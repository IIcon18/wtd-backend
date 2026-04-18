from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.subscription import SubscriptionTier


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    tier: SubscriptionTier
    started_at: datetime
    expires_at: datetime
    is_active: bool
    ai_requests_today: int
    last_request_date: Optional[date]

    model_config = {"from_attributes": True}