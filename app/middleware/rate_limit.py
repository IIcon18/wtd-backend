import logging

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

_LIMIT = 100   # requests per window
_WINDOW = 60   # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:ip:{client_ip}"
        try:
            redis = await get_redis()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, _WINDOW)
            if count > _LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Слишком много запросов, подождите немного"},
                )
        except Exception as exc:
            logger.warning("Rate limit check failed: %s", exc)
        return await call_next(request)


def setup_rate_limit(app: FastAPI) -> None:
    app.add_middleware(RateLimitMiddleware)