"""
Configuration Management
تنظیمات پروژه با استفاده از pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """تنظیمات اصلی پروژه"""

    # Database
    DATABASE_URL: str = "postgresql://admin:password@localhost:5432/reseller_panel"

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
