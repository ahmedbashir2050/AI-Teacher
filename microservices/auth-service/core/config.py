from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_ISSUER: str = "https://accounts.google.com"

    REDIS_URL: str = "redis://redis:6379/0"
    USER_SERVICE_URL: str = "http://user-service:8000"

    class Config:
        extra = "ignore"


settings = Settings()
