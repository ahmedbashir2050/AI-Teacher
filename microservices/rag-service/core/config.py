from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    QDRANT_URL: str = "http://qdrant:6333"
    OPENAI_API_KEY: str

    class Config:
        extra = 'ignore'

settings = Settings()
