import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import check_chat_access, get_current_user
from app.core.exceptions import BadRequestError
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.session_repo import SessionRepository
from app.repositories.swim_profile_repo import SwimProfileRepository
from app.repositories.workout_repo import WorkoutRepository
from app.schemas.chat import ChatHistoryItem, ChatMessage, ChatResponse
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    data: ChatMessage,
    current_user: User = Depends(check_chat_access),
    db: AsyncSession = Depends(get_db),
):
    profile_repo = SwimProfileRepository(db)
    session_repo = SessionRepository(db)
    workout_repo = WorkoutRepository(db)

    profile = await profile_repo.get_by_user_id(current_user.id)
    if not profile:
        raise BadRequestError("Сначала создайте профиль пловца")

    history = await session_repo.get_recent(current_user.id, limit=5)

    # avoid repeating last workout type
    last_type = history[0].workout_type if history else None
    templates = await workout_repo.get_by_level(
        profile.level, limit=3, exclude_type=last_type
    )
    if not templates:
        templates = await workout_repo.get_by_level(profile.level, limit=3)

    reply = await AIService(db).get_ai_response(
        user_message=data.message,
        profile=profile,
        history=history,
        templates=templates,
    )

    # Stage access consumption and session creation in one transaction
    # so neither can succeed without the other.
    tpl = templates[0] if templates else None

    if profile.single_workout_available:
        profile.single_workout_available = False

    session = UserSession(
        user_id=current_user.id,
        workout_type=tpl.type if tpl else "endurance",
        duration_min=tpl.duration_min if tpl else 45,
        distance_m=tpl.content.get("total_distance", 1000) if tpl else 1000,
        content=reply,
    )
    db.add(session)

    await db.commit()
    await db.refresh(session)

    return ChatResponse(reply=reply, session_id=session.id)


@router.get("/history", response_model=List[ChatHistoryItem])
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SessionRepository(db).get_by_user_id(current_user.id, limit=20)