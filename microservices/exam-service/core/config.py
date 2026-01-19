from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    RAG_SERVICE_URL: str = "http://rag-service:8000"

    class Config:
        extra = "ignore"


settings = Settings()
