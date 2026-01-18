from pydantic_settings import BaseSettings

from pathlib import Path
from dotenv import load_dotenv

# Use pathlib to find the project root and load the .env file
# This makes the .env loading robust and independent of the working directory
# from which scripts/apps are run.

project_root = Path(__file__).parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path)


class Settings(BaseSettings):
    # Environment settings
    ENVIRONMENT: str = "development"

    # API keys and URLs
    OPENAI_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379"
    POSTGRES_URL: str
    DATABASE_URL: str
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
    ADMIN_DEFAULT_PASSWORD: str = "admin"
    STUDENT_DEFAULT_PASSWORD: str = "student"

    class Config:
        env_file = dotenv_path
        env_file_encoding = 'utf-8'
        extra = 'ignore'

def get_settings() -> Settings:
    return Settings()

settings = get_settings()
