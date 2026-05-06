import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router
from app.core.redis import close_redis
from app.middleware.cors import setup_cors
from app.middleware.rate_limit import setup_rate_limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _ensure_admin() -> None:
    """Создаёт admin-пользователя из .env если его ещё нет в базе."""
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User, UserRole
    from app.repositories.user_repo import UserRepository

    async with AsyncSessionLocal() as db:
        repo = UserRepository(db)
        existing = await repo.get_by_email(settings.ADMIN_EMAIL)
        if existing:
            # Убедимся что роль admin
            if existing.role != UserRole.admin:
                existing.role = UserRole.admin
                await db.commit()
                logger.info("Updated role to admin for %s", settings.ADMIN_EMAIL)
            return

        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            name="Администратор",
            role=UserRole.admin,
        )
        db.add(admin)
        await db.commit()
        logger.info("Created admin user: %s", settings.ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WavesToDream API starting up")
    await _ensure_admin()
    yield
    await close_redis()
    logger.info("WavesToDream API shut down")


app = FastAPI(
    title="WavesToDream API",
    version="1.0.0",
    description="AI-тренер по плаванию",
    lifespan=lifespan,
)

setup_cors(app)
setup_rate_limit(app)

app.include_router(router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}