from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.payment_repo import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentOut

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentOut, status_code=201)
async def create_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentRepository(db).create(
        user_id=current_user.id,
        tier=data.tier,
        price=data.price,
        screenshot_file_id=data.screenshot_file_id,
    )


@router.get("/me", response_model=List[PaymentOut])
async def get_my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PaymentRepository(db).get_by_user_id(current_user.id)