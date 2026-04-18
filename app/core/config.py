from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://wtd_user:wtd_pass@db:5432/wtd_db"
    REDIS_URL: str = "redis://redis:6379"

    SECRET_KEY: str = "your-secret-key-here-min-32-chars-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AI_API_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    PAYMENT_PHONE: str = ""
    PAYMENT_TG: str = ""

    ADMIN_EMAIL: str = "admin@wavestodream.ru"
    ADMIN_PASSWORD: str = "changeme123"

    CORS_ORIGINS: str = "http://localhost:5173,https://wavestodream.ru"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()