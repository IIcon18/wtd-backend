from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[int] = None


class ChatHistoryItem(BaseModel):
    id: int
    workout_type: str
    duration_min: int
    distance_m: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HistorySaveRequest(BaseModel):
    workout_type: str
    duration_min: int
    distance_m: int
    content: str