from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Books Management System"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str

    REDIS_URL: str
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    CELERY_DEFAULT_QUEUE: str = "scan"
    BOOKS_SCAN_QUEUE: str = "scan"
    BOOKS_ENRICH_QUEUE: str = "enrich"
    BOOKS_MAINTENANCE_QUEUE: str = "maintenance"
    SCAN_JOB_STALLED_SECONDS: int = 1800
    SCAN_ITEM_STALLED_SECONDS: int = 1800
    MAINTENANCE_RECONCILE_INTERVAL_SECONDS: int = 300

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = ""

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:19006"]

    BOOKS_DIR: str = "/app/books"
    UPLOADS_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 104857600

    DOUBAN_API_URL: str = "https://douban.uieee.com"
    GOOGLE_BOOKS_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
