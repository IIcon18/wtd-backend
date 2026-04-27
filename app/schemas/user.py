from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None