"""
Configuration settings for ABE Portal
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "ABE Portal"
    DEBUG: bool = False
    
    # Security
    JWT_SECRET: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    POSTGRES_DSN: str = "postgresql+psycopg://abeportal:password@localhost:5432/abeportal"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Paperless-ngx
    PAPERLESS_BASE_URL: str = "http://localhost:8000"
    PAPERLESS_API_TOKEN: str = ""
    
    # Upload
    MAX_UPLOAD_MB: int = 50
    ENABLE_STANDALONE_OCR: bool = False
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MIN: int = 10
    RATE_LIMIT_SEARCH_PER_MIN: int = 60
    RATE_LIMIT_DOWNLOAD_PER_MIN: int = 60
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Admin Bootstrap
    ADMIN_USERNAME: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    
    # Search
    SEARCH_RESULTS_LIMIT: int = 50
    ENUMBER_SEARCH_TOLERANCE: float = 0.8
    
    # Audit
    AUDIT_RETENTION_DAYS: int = 365
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
