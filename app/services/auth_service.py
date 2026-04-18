import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)

_REFRESH_PREFIX = "refresh:"


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, name: str) -> TokenResponse:
        repo = UserRepository(self.db)
        if await repo.get_by_email(email):
            raise ConflictError("Email уже зарегистрирован")
        hashed = hash_password(password)
        user = await repo.create(email=email, hashed_password=hashed, name=name)
        return await self._issue_tokens(user.id)

    async def login(self, email: str, password: str) -> TokenResponse:
        repo = UserRepository(self.db)
        user = await repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Неверный email или пароль")
        if not user.is_active:
            raise UnauthorizedError("Аккаунт заблокирован")
        return await self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Недействительный refresh токен")

        jti = payload.get("jti")
        redis = await get_redis()
        stored = await redis.get(f"{_REFRESH_PREFIX}{jti}")
        if not stored:
            raise UnauthorizedError("Refresh токен истёк или отозван")

        user_id = int(payload["sub"])
        # rotate: delete old, issue new
        await redis.delete(f"{_REFRESH_PREFIX}{jti}")
        return await self._issue_tokens(user_id)

    async def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if payload and payload.get("jti"):
            redis = await get_redis()
            await redis.delete(f"{_REFRESH_PREFIX}{payload['jti']}")
            logger.info("Logged out user_id=%s", payload.get("sub"))

    async def _issue_tokens(self, user_id: int) -> TokenResponse:
        access_token = create_access_token(user_id)
        refresh_token, jti = create_refresh_token(user_id)

        redis = await get_redis()
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await redis.setex(f"{_REFRESH_PREFIX}{jti}", ttl, str(user_id))

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)