"""
Account Service
سرویس مدیریت اکانت‌های مشتریان
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from ..models import (
    CustomerAccount, AccountStatus, AccountSyncLog,
    Reseller, ResellerProductAccess, Product, ServicePlan,
    OperationType
)
from .credit_service import CreditService
from .panel_integrations import PanelIntegrationFactory, PanelOperationError
from ..utils.security import generate_username, decrypt_data

logger = logging.getLogger(__name__)


class AccountService:
    """سرویس مدیریت اکانت‌های مشتریان"""

    @staticmethod
    async def create_account(
        db: Session,
        reseller_id: str,
        product_id: str,
        service_plan_id: str,
        username: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_note: Optional[str] = None
    ) -> tuple[CustomerAccount, str]:
        """
        ایجاد اکانت جدید

        Returns:
            tuple: (اکانت ایجاد شده, لینک اشتراک)

        Raises:
            ValueError: اگر دسترسی نباشد یا کریدیت کافی نباشد
            PanelOperationError: اگر خطا در ایجاد در پنل رخ دهد
        """
        # 1. بررسی دسترسی نماینده به محصول
        access = db.query(ResellerProductAccess).filter(
            ResellerProductAccess.reseller_id == reseller_id,
            ResellerProductAccess.product_id == product_id,
            ResellerProductAccess.is_active == True
        ).first()

        if not access:
            raise ValueError("شما به این محصول دسترسی ندارید")

        # بررسی محدودیت تعداد اکانت
        if access.max_accounts and access.current_accounts >= access.max_accounts:
            raise ValueError(f"به حداکثر تعداد اکانت مجاز رسیده‌اید ({access.max_accounts})")

        # 2. دریافت اطلاعات محصول و پلن
        product = db.query(Product).get(product_id)
        plan = db.query(ServicePlan).get(service_plan_id)

        if not product or not product.is_active:
            raise ValueError("محصول یافت نشد یا غیرفعال است")

        if not plan or not plan.is_active:
            raise ValueError("پلن سرویس یافت نشد یا غیرفعال است")

        # 3. محاسبه هزینه و کسر کریدیت
        try:
            transaction, cost = CreditService.charge_for_operation(
                db=db,
                reseller_id=reseller_id,
                operation_type=OperationType.CREATE_ACCOUNT,
                product_group_id=str(access.product_group_id),
                service_plan_id=service_plan_id,
                product_id=product_id
            )
        except ValueError as e:
            raise ValueError(f"خطا در کسر کریدیت: {str(e)}")

        # 4. تولید username اگر نباشد
        if not username:
            username = generate_username()

        # 5. ایجاد اکانت در پنل
        subscription_url = None
        panel_account_id = None

        if product.requires_panel_connection:
            try:
                # دریافت اتصال پنل
                panel_conn = db.query(ResellerProductAccess).filter(
                    ResellerProductAccess.id == access.id
                ).first().panel_connection

                if not panel_conn:
                    raise ValueError("اتصال به پنل یافت نشد")

                # رمزگشایی credentials
                credentials = decrypt_data(panel_conn.credentials)

                # ایجاد integration
                integration = PanelIntegrationFactory.create(
                    panel_type=panel_conn.panel_type,
                    connection_config={
                        "base_url": panel_conn.base_url,
                        "username": credentials["username"],
                        "password": credentials["password"]
                    }
                )

                # ایجاد کاربر در پنل
                panel_result = await integration.create_user(
                    username=username,
                    data_limit_gb=plan.data_limit_gb,
                    expire_days=plan.duration_days,
                    device_limit=plan.device_limit
                )

                panel_account_id = panel_result["panel_id"]
                subscription_url = panel_result.get("subscription_url")

                logger.info(f"Account created in panel: {username}")

            except Exception as e:
                # اگر ایجاد در پنل fail شد، کریدیت را برگردان
                logger.error(f"Failed to create account in panel: {e}")

                CreditService.refund_credit(
                    db=db,
                    reseller_id=reseller_id,
                    amount=cost,
                    product_id=product_id,
                    reason=f"برگشت به دلیل خطا در ایجاد: {str(e)}"
                )

                raise PanelOperationError(f"خطا در ایجاد اکانت در پنل: {str(e)}")

        # 6. ذخیره در دیتابیس
        account = CustomerAccount(
            reseller_id=reseller_id,
            product_id=product_id,
            service_plan_id=service_plan_id,
            username=username,
            panel_account_id=panel_account_id,
            subscription_url=subscription_url,
            customer_name=customer_name,
            customer_note=customer_note,
            data_limit_gb=plan.data_limit_gb,
            expire_date=datetime.utcnow() + timedelta(days=plan.duration_days),
            device_limit=plan.device_limit,
            status=AccountStatus.ACTIVE,
            credit_cost=cost
        )

        db.add(account)

        # لینک تراکنش به اکانت
        if transaction:
            transaction.related_account_id = account.id

        # بروزرسانی تعداد اکانت‌های نماینده
        access.current_accounts += 1

        # بروزرسانی آمار نماینده
        reseller = db.query(Reseller).filter(Reseller.user_id == reseller_id).first()
        if reseller:
            reseller.total_accounts_created += 1

        # ثبت log
        sync_log = AccountSyncLog(
            account_id=account.id,
            sync_type="create",
            status="success",
            message=f"اکانت با موفقیت ایجاد شد"
        )
        db.add(sync_log)

        db.commit()
        db.refresh(account)

        logger.info(f"Account created successfully: {username} for reseller {reseller_id}")

        return account, subscription_url

    @staticmethod
    async def delete_account(
        db: Session,
        account_id: str,
        reseller_id: str
    ) -> Decimal:
        """
        حذف اکانت با برگشت کریدیت

        Returns:
            Decimal: مقدار کریدیت برگشت داده شده

        Raises:
            ValueError: اگر اکانت یافت نشود یا متعلق به نماینده نباشد
        """
        # دریافت اکانت
        account = db.query(CustomerAccount).get(account_id)

        if not account:
            raise ValueError("اکانت یافت نشد")

        if str(account.reseller_id) != reseller_id:
            raise ValueError("این اکانت متعلق به شما نیست")

        if account.status == AccountStatus.DELETED:
            raise ValueError("این اکانت قبلاً حذف شده است")

        # محاسبه برگشت کریدیت
        refund_amount = AccountService._calculate_refund(account)

        # حذف از پنل
        product = db.query(Product).get(account.product_id)

        if product and product.requires_panel_connection:
            try:
                # دریافت اتصال پنل
                access = db.query(ResellerProductAccess).filter(
                    ResellerProductAccess.reseller_id == reseller_id,
                    ResellerProductAccess.product_id == account.product_id
                ).first()

                if access and access.panel_connection:
                    panel_conn = access.panel_connection
                    credentials = decrypt_data(panel_conn.credentials)

                    integration = PanelIntegrationFactory.create(
                        panel_type=panel_conn.panel_type,
                        connection_config={
                            "base_url": panel_conn.base_url,
                            "username": credentials["username"],
                            "password": credentials["password"]
                        }
                    )

                    await integration.delete_user(account.username)
                    logger.info(f"Account deleted from panel: {account.username}")

            except Exception as e:
                logger.error(f"Failed to delete account from panel: {e}")
                # ادامه می‌دهیم، چون حذف از دیتابیس مهم‌تر است

        # برگشت کریدیت
        if refund_amount > 0:
            CreditService.refund_credit(
                db=db,
                reseller_id=reseller_id,
                amount=refund_amount,
                account_id=account_id,
                product_id=account.product_id,
                reason=f"برگشت کریدیت حذف اکانت {account.username}"
            )

        # علامت‌گذاری به عنوان حذف شده
        account.status = AccountStatus.DELETED
        account.deleted_at = datetime.utcnow()

        # کاهش تعداد اکانت‌های نماینده
        access = db.query(ResellerProductAccess).filter(
            ResellerProductAccess.reseller_id == reseller_id,
            ResellerProductAccess.product_id == account.product_id
        ).first()

        if access:
            access.current_accounts = max(0, access.current_accounts - 1)

        # ثبت log
        sync_log = AccountSyncLog(
            account_id=account.id,
            sync_type="delete",
            status="success",
            message=f"اکانت حذف شد. کریدیت برگشتی: {refund_amount}"
        )
        db.add(sync_log)

        db.commit()

        logger.info(f"Account deleted: {account.username}, refund: {refund_amount}")

        return refund_amount

    @staticmethod
    def _calculate_refund(account: CustomerAccount) -> Decimal:
        """
        محاسبه مقدار کریدیت قابل برگشت
        بر اساس زمان باقیمانده و حجم استفاده نشده
        """
        if account.credit_cost <= 0:
            return Decimal(0)

        # محاسبه نسبت زمان
        total_seconds = (account.expire_date - account.created_at).total_seconds()
        elapsed_seconds = (datetime.utcnow() - account.created_at).total_seconds()
        remaining_seconds = max(0, total_seconds - elapsed_seconds)
        time_ratio = remaining_seconds / total_seconds if total_seconds > 0 else 0

        # محاسبه نسبت حجم (اگر محدود باشد)
        data_ratio = 1.0
        if account.data_limit_gb:
            data_used_gb = account.data_used_bytes / (1024 ** 3)
            data_remaining_gb = max(0, account.data_limit_gb - data_used_gb)
            data_ratio = data_remaining_gb / account.data_limit_gb

        # میانگین وزنی (60% زمان، 40% حجم)
        refund_ratio = (time_ratio * 0.6) + (data_ratio * 0.4)

        # برگشت 80% از مقدار محاسبه شده
        refund_amount = account.credit_cost * Decimal(str(refund_ratio)) * Decimal("0.8")

        return round(refund_amount, 2)

    @staticmethod
    async def renew_account(
        db: Session,
        account_id: str,
        reseller_id: str,
        days: int
    ) -> CustomerAccount:
        """
        تمدید اکانت (افزودن زمان)

        Raises:
            ValueError: اگر اکانت یافت نشود یا کریدیت کافی نباشد
        """
        account = db.query(CustomerAccount).get(account_id)

        if not account or str(account.reseller_id) != reseller_id:
            raise ValueError("اکانت یافت نشد")

        if account.status == AccountStatus.DELETED:
            raise ValueError("اکانت حذف شده قابل تمدید نیست")

        # دریافت access برای محاسبه هزینه
        access = db.query(ResellerProductAccess).filter(
            ResellerProductAccess.reseller_id == reseller_id,
            ResellerProductAccess.product_id == account.product_id
        ).first()

        if not access:
            raise ValueError("دسترسی به محصول یافت نشد")

        # محاسبه هزینه (نسبی بر اساس پلن اصلی)
        plan = db.query(ServicePlan).get(account.service_plan_id)
        cost_per_day = plan.credit_cost / plan.duration_days
        renew_cost = cost_per_day * days

        # کسر کریدیت
        CreditService.charge_for_operation(
            db=db,
            reseller_id=reseller_id,
            operation_type=OperationType.RENEW,
            product_group_id=str(access.product_group_id),
            service_plan_id=str(account.service_plan_id),
            account_id=account_id,
            product_id=account.product_id
        )

        # تمدید در پنل
        product = db.query(Product).get(account.product_id)

        if product and product.requires_panel_connection:
            try:
                panel_conn = access.panel_connection
                credentials = decrypt_data(panel_conn.credentials)

                integration = PanelIntegrationFactory.create(
                    panel_type=panel_conn.panel_type,
                    connection_config={
                        "base_url": panel_conn.base_url,
                        "username": credentials["username"],
                        "password": credentials["password"]
                    }
                )

                await integration.extend_user_time(account.username, days)
                logger.info(f"Account renewed in panel: {account.username}")

            except Exception as e:
                logger.error(f"Failed to renew in panel: {e}")
                raise PanelOperationError(f"خطا در تمدید در پنل: {str(e)}")

        # بروزرسانی در دیتابیس
        account.expire_date = account.expire_date + timedelta(days=days)
        account.updated_at = datetime.utcnow()

        if account.status == AccountStatus.EXPIRED:
            account.status = AccountStatus.ACTIVE

        # ثبت log
        sync_log = AccountSyncLog(
            account_id=account.id,
            sync_type="renew",
            status="success",
            message=f"اکانت {days} روز تمدید شد"
        )
        db.add(sync_log)

        db.commit()
        db.refresh(account)

        logger.info(f"Account renewed: {account.username}, +{days} days")

        return account

    @staticmethod
    async def add_traffic(
        db: Session,
        account_id: str,
        reseller_id: str,
        gb: int
    ) -> CustomerAccount:
        """
        افزودن حجم به اکانت
        """
        account = db.query(CustomerAccount).get(account_id)

        if not account or str(account.reseller_id) != reseller_id:
            raise ValueError("اکانت یافت نشد")

        if account.data_limit_gb is None:
            raise ValueError("این اکانت حجم نامحدود دارد")

        # کسر کریدیت
        access = db.query(ResellerProductAccess).filter(
            ResellerProductAccess.reseller_id == reseller_id,
            ResellerProductAccess.product_id == account.product_id
        ).first()

        CreditService.charge_for_operation(
            db=db,
            reseller_id=reseller_id,
            operation_type=OperationType.ADD_TRAFFIC,
            product_group_id=str(access.product_group_id),
            service_plan_id=str(account.service_plan_id),
            account_id=account_id,
            product_id=account.product_id
        )

        # افزودن حجم در پنل
        product = db.query(Product).get(account.product_id)

        if product and product.requires_panel_connection:
            try:
                panel_conn = access.panel_connection
                credentials = decrypt_data(panel_conn.credentials)

                integration = PanelIntegrationFactory.create(
                    panel_type=panel_conn.panel_type,
                    connection_config={
                        "base_url": panel_conn.base_url,
                        "username": credentials["username"],
                        "password": credentials["password"]
                    }
                )

                await integration.add_user_traffic(account.username, gb)

            except Exception as e:
                raise PanelOperationError(f"خطا در افزودن حجم: {str(e)}")

        # بروزرسانی
        account.data_limit_gb += gb
        account.updated_at = datetime.utcnow()

        sync_log = AccountSyncLog(
            account_id=account.id,
            sync_type="add_traffic",
            status="success",
            message=f"{gb}GB حجم افزوده شد"
        )
        db.add(sync_log)

        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    async def toggle_status(
        db: Session,
        account_id: str,
        reseller_id: str,
        enabled: bool
    ) -> CustomerAccount:
        """
        فعال/غیرفعال کردن اکانت
        """
        account = db.query(CustomerAccount).get(account_id)

        if not account or str(account.reseller_id) != reseller_id:
            raise ValueError("اکانت یافت نشد")

        # تغییر وضعیت در پنل
        product = db.query(Product).get(account.product_id)

        if product and product.requires_panel_connection:
            access = db.query(ResellerProductAccess).filter(
                ResellerProductAccess.reseller_id == reseller_id,
                ResellerProductAccess.product_id == account.product_id
            ).first()

            try:
                panel_conn = access.panel_connection
                credentials = decrypt_data(panel_conn.credentials)

                integration = PanelIntegrationFactory.create(
                    panel_type=panel_conn.panel_type,
                    connection_config={
                        "base_url": panel_conn.base_url,
                        "username": credentials["username"],
                        "password": credentials["password"]
                    }
                )

                await integration.toggle_user_status(account.username, enabled)

            except Exception as e:
                raise PanelOperationError(f"خطا در تغییر وضعیت: {str(e)}")

        # بروزرسانی
        account.status = AccountStatus.ACTIVE if enabled else AccountStatus.INACTIVE
        account.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    async def sync_from_panel(
        db: Session,
        account_id: str
    ) -> CustomerAccount:
        """
        همگام‌سازی اطلاعات اکانت از پنل
        """
        account = db.query(CustomerAccount).get(account_id)

        if not account:
            raise ValueError("اکانت یافت نشد")

        product = db.query(Product).get(account.product_id)

        if not product or not product.requires_panel_connection:
            return account

        try:
            access = db.query(ResellerProductAccess).filter(
                ResellerProductAccess.reseller_id == account.reseller_id,
                ResellerProductAccess.product_id == account.product_id
            ).first()

            panel_conn = access.panel_connection
            credentials = decrypt_data(panel_conn.credentials)

            integration = PanelIntegrationFactory.create(
                panel_type=panel_conn.panel_type,
                connection_config={
                    "base_url": panel_conn.base_url,
                    "username": credentials["username"],
                    "password": credentials["password"]
                }
            )

            usage = await integration.get_user_usage(account.username)

            # بروزرسانی داده‌ها
            account.data_used_bytes = usage.get("used_bytes", 0)
            account.last_synced = datetime.utcnow()
            account.sync_data = usage

            # بررسی انقضا
            if account.is_expired and account.status == AccountStatus.ACTIVE:
                account.status = AccountStatus.EXPIRED

            sync_log = AccountSyncLog(
                account_id=account.id,
                sync_type="auto",
                status="success",
                message="همگام‌سازی موفق",
                synced_data=usage
            )
            db.add(sync_log)

            db.commit()
            db.refresh(account)

            logger.info(f"Account synced: {account.username}")

        except Exception as e:
            logger.error(f"Sync failed for {account.username}: {e}")

            sync_log = AccountSyncLog(
                account_id=account.id,
                sync_type="auto",
                status="failed",
                message=str(e)
            )
            db.add(sync_log)
            db.commit()

        return account

    @staticmethod
    def get_accounts(
        db: Session,
        reseller_id: str,
        status: Optional[AccountStatus] = None,
        product_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CustomerAccount]:
        """
        دریافت لیست اکانت‌های نماینده
        """
        query = db.query(CustomerAccount).filter(
            CustomerAccount.reseller_id == reseller_id
        )

        if status:
            query = query.filter(CustomerAccount.status == status)

        if product_id:
            query = query.filter(CustomerAccount.product_id == product_id)

        query = query.order_by(CustomerAccount.created_at.desc())
        query = query.offset(offset).limit(limit)

        return query.all()
