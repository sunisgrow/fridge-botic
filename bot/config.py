"""Bot configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot settings from environment variables."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str 

    # API
    API_URL: str 
    API_EXTERNAL_URL: str 

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
