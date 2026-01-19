from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"

    # S3 / MinIO Configuration
    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "books"
    S3_REGION: str = "us-east-1"

    # Internal Services
    RAG_SERVICE_URL: str = "http://rag-service:8000"
    USER_SERVICE_URL: str = "http://user-service:8000"

    # Auth context
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    class Config:
        extra = "ignore"


settings = Settings()
