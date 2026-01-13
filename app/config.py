import os
from pydantic_settings import BaseSettings
from typing import ClassVar

class Settings(BaseSettings):
    # Environment settings
    ENVIRONMENT: str = "development"

    # API keys and URLs
    OPENAI_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379"
    POSTGRES_URL: str
    SENTRY_DSN: str = ""

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    # Celery settings
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Data retention settings
    CHAT_HISTORY_RETENTION_DAYS: int = 30

    # Default user passwords
    ADMIN_DEFAULT_PASSWORD: str = "adminpassword"
    STUDENT_DEFAULT_PASSWORD: str = "studentpassword"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

def get_settings() -> Settings:
    return Settings()

settings = get_settings()
