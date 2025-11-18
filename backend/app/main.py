"""
Main Application File
نقطه ورودی اصلی برنامه FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import engine, Base

# Import routers
from .api import auth, reseller
from .api.admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events
    اجرا در startup و shutdown
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # ایجاد جداول (در production از Alembic استفاده کن)
    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created")

    # راه‌اندازی scheduler (بعداً اضافه می‌شود)
    # if settings.ENABLE_SCHEDULER:
    #     from .services.scheduler import start_scheduler
    #     start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down application")


# ایجاد Application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="پنل مدیریت نمایندگی محصولات - Multi-Product Reseller Management Panel",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoint
@app.get("/health")
async def health_check():
    """بررسی سلامت سرویس"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "Disabled in production"
    }


# Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/api/admin")
app.include_router(reseller.router, prefix="/api/reseller", tags=["Reseller"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
