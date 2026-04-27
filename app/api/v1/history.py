from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.schemas.chat import ChatHistoryItem, HistorySaveRequest

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/", response_model=List[ChatHistoryItem])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SessionRepository(db).get_by_user_id(current_user.id)


@router.get("/{session_id}", response_model=ChatHistoryItem)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await SessionRepository(db).get_by_id(session_id)
    if not session:
        raise NotFoundError("Сессия не найдена")
    if session.user_id != current_user.id:
        raise ForbiddenError()
    return session


@router.post("/save", response_model=ChatHistoryItem, status_code=201)
async def save_session(
    data: HistorySaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SessionRepository(db).create(
        user_id=current_user.id,
        workout_type=data.workout_type,
        duration_min=data.duration_min,
        distance_m=data.distance_m,
        content=data.content,
    )