"""Bot configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot settings from environment variables."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # API
    API_URL: str = "http://localhost:8000/api/v1"
    API_EXTERNAL_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fridge_bot"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
