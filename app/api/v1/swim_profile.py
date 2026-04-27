from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.swim_profile_repo import SwimProfileRepository
from app.schemas.swim_profile import SwimProfileCreate, SwimProfileOut, SwimProfileUpdate

router = APIRouter(prefix="/swim-profile", tags=["swim-profile"])


@router.get("/me", response_model=SwimProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await SwimProfileRepository(db).get_by_user_id(current_user.id)
    if not profile:
        raise NotFoundError("Профиль пловца не найден")
    return profile


@router.post("/", response_model=SwimProfileOut, status_code=201)
async def create_profile(
    data: SwimProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SwimProfileRepository(db)
    if await repo.get_by_user_id(current_user.id):
        raise ConflictError("Профиль уже существует")
    return await repo.create(user_id=current_user.id, **data.model_dump())


@router.patch("/me", response_model=SwimProfileOut)
async def update_profile(
    data: SwimProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SwimProfileRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise NotFoundError("Профиль пловца не найден")
    updates = data.model_dump(exclude_none=True)
    if updates:
        profile = await repo.update(profile, **updates)
    return profile