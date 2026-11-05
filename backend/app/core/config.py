"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "mysql+aiomysql://moodhunter:moodhunter_pass@localhost:3306/moodhunter_db"
    DB_ECHO: bool = False

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_TIMEOUT_SECONDS: float = 5.0
    LLM_CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 3
    LLM_CIRCUIT_BREAKER_RESET_SECONDS: int = 60


@lru_cache()
def get_settings() -> Settings:
    return Settings()
