import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).register(data.email, data.password, data.name)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(data.refresh_token)