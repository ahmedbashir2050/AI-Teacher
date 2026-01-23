from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    REDIS_URL: str = "redis://redis:6379/0"
    RAG_SERVICE_URL: str = "http://rag-service:8000"

    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "ai-teacher-audience"
    JWT_ISSUER: str = "ai-teacher-auth-service"

    class Config:
        case_sensitive = True
        extra = "ignore"


settings = Settings()
