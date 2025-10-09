from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Books Management System"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:19006"]
    
    # File Storage
    BOOKS_DIR: str = "/app/books"
    UPLOADS_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    
    # External APIs
    DOUBAN_API_URL: str = "https://douban.uieee.com"
    GOOGLE_BOOKS_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
