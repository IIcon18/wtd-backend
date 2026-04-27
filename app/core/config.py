from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AI_API_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    # GigaChat (Sberbank) — приоритет над AI_API_URL
    GIGACHAT_CREDENTIALS: str = ""  # base64(client_id:client_secret) из личного кабинета
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"  # GIGACHAT_API_PERS или GIGACHAT_API_CORP
    GIGACHAT_MODEL: str = "GigaChat"

    PAYMENT_PHONE: str = ""
    PAYMENT_TG: str = ""

    ADMIN_EMAIL: str = "admin@wavestodream.ru"
    ADMIN_PASSWORD: str

    CORS_ORIGINS: str = "http://localhost:5173,http://wavestodream.pe4en1e.ru"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()