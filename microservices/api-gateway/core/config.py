from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    REDIS_URL: str

    # Service URLs
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    USER_SERVICE_URL: str = "http://user-service:8000"
    CHAT_SERVICE_URL: str = "http://chat-service:8000"
    RAG_SERVICE_URL: str = "http://rag-service:8000"
    EXAM_SERVICE_URL: str = "http://exam-service:8000"

    class Config:
        extra = "ignore"


settings = Settings()
