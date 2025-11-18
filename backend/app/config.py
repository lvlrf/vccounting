"""
Configuration Management
تنظیمات پروژه با استفاده از pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """تنظیمات اصلی پروژه"""

    # Database (MySQL)
    DATABASE_URL: str = "mysql+pymysql://admin:password@localhost:3306/reseller_panel?charset=utf8mb4"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # Encryption
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)

    # Application
    DEBUG: bool = True
    APP_NAME: str = "Reseller Management Panel"
    APP_VERSION: str = "1.0.0"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080"
    ]

    # Admin Default User
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@example.com"

    # Background Jobs
    ENABLE_SCHEDULER: bool = True
    SYNC_ACCOUNTS_INTERVAL_HOURS: int = 1

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
