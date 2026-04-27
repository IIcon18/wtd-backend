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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WavesToDream API starting up")
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