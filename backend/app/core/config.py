from typing import List

from pydantic import field_validator
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

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_allowed_origins(cls, value):
        # Accept three input shapes from the environment:
        #   - JSON list      (pydantic's default for List[str] from env)
        #   - comma-separated "a,b,c"
        #   - already a list (programmatic instantiation in tests)
        if value is None or isinstance(value, list):
            return value
        text = str(value).strip()
        if not text:
            return []
        if text.startswith("["):
            # Let pydantic's normal JSON parser handle it.
            return text
        return [item.strip() for item in text.split(",") if item.strip()]

    BOOKS_DIR: str = "/app/books"
    UPLOADS_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 104857600

    DOUBAN_API_URL: str = "https://douban.uieee.com"
    GOOGLE_BOOKS_API_KEY: str = ""

    # Phase-2 search backend (optional). When MEILI_URL is empty the
    # application falls back to PostgreSQL FTS exclusively.
    MEILI_URL: str = ""
    MEILI_MASTER_KEY: str = ""

    # Rate limiting (requests / minute / client IP). 0 disables.
    RATE_LIMIT_PER_MINUTE: int = 0

    # Caching. CACHE_TTL_SECONDS is 0 to disable by default.
    CACHE_TTL_SECONDS: int = 0

    # Observability
    METRICS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
