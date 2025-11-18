"""
Celery Tasks
وظایف Asynchronous برای Job Queue
"""
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from .database import SessionLocal
from .models import CustomerAccount, AccountStatus, AccountSyncLog
from .services.account_service import AccountService

logger = logging.getLogger(__name__)


def get_db():
    """دریافت database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # session باز می‌ماند تا task تمام شود


@shared_task(name="app.tasks.create_account_task")
def create_account_task(
    reseller_id: str,
    product_id: str,
    service_plan_id: str,
    username: str = None,
    customer_name: str = None,
    customer_note: str = None
):
    """
    Task ایجاد اکانت (Async)

    با استفاده از Celery، ایجاد اکانت در صف قرار می‌گیرد
    و اگر خطا رخ دهد، retry می‌شود
    """
    db = get_db()

    try:
        import asyncio
        account, subscription_url = asyncio.run(
            AccountService.create_account(
                db=db,
                reseller_id=reseller_id,
                product_id=product_id,
                service_plan_id=service_plan_id,
                username=username,
                customer_name=customer_name,
                customer_note=customer_note
            )
        )

        logger.info(f"Account created successfully via Celery: {account.username}")

        return {
            "status": "success",
            "account_id": str(account.id),
            "username": account.username,
            "subscription_url": subscription_url
        }

    except Exception as e:
        logger.error(f"Failed to create account via Celery: {e}")
        raise  # Celery خودش retry می‌کند

    finally:
        db.close()


@shared_task(name="app.tasks.sync_account_task", bind=True, max_retries=3)
def sync_account_task(self, account_id: str):
    """
    Task همگام‌سازی یک اکانت از پنل
    """
    db = get_db()

    try:
        import asyncio
        account = asyncio.run(
            AccountService.sync_from_panel(
                db=db,
                account_id=account_id
            )
        )

        logger.info(f"Account synced successfully: {account.username}")

        return {
            "status": "success",
            "account_id": str(account.id),
            "data_used_gb": account.data_used_gb
        }

    except Exception as e:
        logger.error(f"Failed to sync account {account_id}: {e}")

        # Retry با exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()


@shared_task(name="app.tasks.sync_all_accounts_task")
def sync_all_accounts_task():
    """
    Task همگام‌سازی تمام اکانت‌های فعال
    این task توسط Celery Beat به صورت دوره‌ای اجرا می‌شود
    """
    db = get_db()

    try:
        # دریافت تمام اکانت‌های فعال
        accounts = db.query(CustomerAccount).filter(
            CustomerAccount.status.in_([AccountStatus.ACTIVE, AccountStatus.INACTIVE])
        ).all()

        logger.info(f"Starting sync for {len(accounts)} accounts")

        synced_count = 0
        failed_count = 0

        for account in accounts:
            try:
                # اضافه کردن هر اکانت به صف برای همگام‌سازی
                sync_account_task.delay(str(account.id))
                synced_count += 1

            except Exception as e:
                logger.error(f"Failed to queue sync for account {account.id}: {e}")
                failed_count += 1

        logger.info(f"Sync queued: {synced_count} success, {failed_count} failed")

        return {
            "status": "completed",
            "synced": synced_count,
            "failed": failed_count
        }

    finally:
        db.close()


@shared_task(name="app.tasks.check_expired_accounts_task")
def check_expired_accounts_task():
    """
    بررسی و علامت‌گذاری اکانت‌های منقضی شده
    اجرا می‌شود هر روز ساعت 00:00
    """
    db = get_db()

    try:
        # پیدا کردن اکانت‌های منقضی شده
        expired_accounts = db.query(CustomerAccount).filter(
            CustomerAccount.expire_date < datetime.utcnow(),
            CustomerAccount.status == AccountStatus.ACTIVE
        ).all()

        logger.info(f"Found {len(expired_accounts)} expired accounts")

        for account in expired_accounts:
            account.status = AccountStatus.EXPIRED

            # ثبت log
            log = AccountSyncLog(
                account_id=account.id,
                sync_type="auto_expire",
                status="success",
                message="اکانت به دلیل انقضا غیرفعال شد"
            )
            db.add(log)

        db.commit()

        logger.info(f"Marked {len(expired_accounts)} accounts as expired")

        return {
            "status": "completed",
            "expired_count": len(expired_accounts)
        }

    finally:
        db.close()


@shared_task(name="app.tasks.cleanup_old_logs_task")
def cleanup_old_logs_task(days=30):
    """
    پاکسازی لاگ‌های قدیمی‌تر از X روز
    برای جلوگیری از پر شدن دیتابیس
    """
    db = get_db()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # حذف لاگ‌های قدیمی
        deleted = db.query(AccountSyncLog).filter(
            AccountSyncLog.created_at < cutoff_date
        ).delete()

        db.commit()

        logger.info(f"Cleaned up {deleted} old logs (older than {days} days)")

        return {
            "status": "completed",
            "deleted_count": deleted
        }

    finally:
        db.close()


@shared_task(name="app.tasks.delete_account_task")
def delete_account_task(account_id: str, reseller_id: str):
    """
    Task حذف اکانت (Async)
    """
    db = get_db()

    try:
        import asyncio
        refund_amount = asyncio.run(
            AccountService.delete_account(
                db=db,
                account_id=account_id,
                reseller_id=reseller_id
            )
        )

        logger.info(f"Account deleted successfully via Celery: {account_id}")

        return {
            "status": "success",
            "account_id": account_id,
            "refund_amount": float(refund_amount)
        }

    except Exception as e:
        logger.error(f"Failed to delete account via Celery: {e}")
        raise

    finally:
        db.close()
