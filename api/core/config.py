from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Finance Management Api"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENABLE_SEED: bool = False

    # Must be set in .env / Render environment variables
    DATABASE_URL: str
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    TOTP_ISSUER: str = "NairaFlow"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    APPLE_CLIENT_ID: str = ""

    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@nairaflow.com"

    PAYSTACK_SECRET_KEY: str = ""
    FLUTTERWAVE_SECRET_KEY: str = ""

    UPLOAD_DIR: str = "uploads/avatars"
    MAX_AVATAR_SIZE_MB: int = 2
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()