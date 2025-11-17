"""
Database Configuration
تنظیمات اتصال به دیتابیس و session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# ایجاد Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # بررسی سلامت connection قبل از استفاده
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG  # نمایش SQL queries در حالت debug
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base برای مدل‌ها
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency برای دریافت database session در FastAPI endpoints

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    ایجاد جداول دیتابیس
    این تابع را فقط برای تست استفاده کن
    در production از Alembic استفاده کن
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
