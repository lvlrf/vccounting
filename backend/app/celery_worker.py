"""
Celery Worker Configuration
مدیریت Job Queue با Celery و Redis
"""
from celery import Celery
from celery.schedules import crontab
import logging

from .config import settings

logger = logging.getLogger(__name__)

# ایجاد Celery app
celery_app = Celery(
    "reseller_panel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# تنظیمات Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,  # یک task در یک زمان
    worker_max_tasks_per_child=1000,  # بعد از 1000 task، worker restart شود
)

# تنظیمات Celery Beat (Periodic Tasks)
celery_app.conf.beat_schedule = {
    'sync-all-accounts': {
        'task': 'app.tasks.sync_all_accounts_task',
        'schedule': crontab(minute='*/30'),  # هر 30 دقیقه
    },
    'check-expired-accounts': {
        'task': 'app.tasks.check_expired_accounts_task',
        'schedule': crontab(hour=0, minute=0),  # هر روز ساعت 00:00
    },
    'cleanup-old-logs': {
        'task': 'app.tasks.cleanup_old_logs_task',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # هفته‌ای یکبار ساعت 02:00
    },
}

logger.info("Celery configured successfully")
