from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    QDRANT_URL: str = "http://qdrant:6333"
    REDIS_URL: str = "redis://redis:6379/0"
    OPENAI_API_KEY: str

    class Config:
        extra = 'ignore'

settings = Settings()
