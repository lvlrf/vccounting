"""
Marzban Panel Integration
اتصال به Marzban Panel با استفاده از OpexCore
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

from .base import BasePanelIntegration, PanelConnectionError, PanelUserNotFoundError, PanelOperationError

logger = logging.getLogger(__name__)


class MarzbanIntegration(BasePanelIntegration):
    """
    پیاده‌سازی اتصال به Marzban Panel
    استفاده از OpexCore library: https://github.com/erfjab/OpexCore
    """

    def __init__(self, base_url: str, username: str, password: str):
        super().__init__(base_url, username, password)
        self.api = None
        self._init_api()

    def _init_api(self):
        """راه‌اندازی API client"""
        try:
            # Import OpexCore
            from opexcore import MarzbanAPI

            self.api = MarzbanAPI(
                base_url=self.base_url,
                username=self.username,
                password=self.password
            )
            logger.info(f"Marzban API initialized for {self.base_url}")
        except ImportError:
            logger.error("OpexCore not installed. Install: pip install git+https://github.com/erfjab/OpexCore.git")
            raise PanelConnectionError("OpexCore library not found")
        except Exception as e:
            logger.error(f"Failed to initialize Marzban API: {e}")
            raise PanelConnectionError(f"Failed to initialize API: {e}")

    async def test_connection(self) -> bool:
        """تست اتصال به پنل"""
        try:
            # تست با دریافت آمار سیستم
            stats = await self.api.get_system_stats()
            logger.info(f"Marzban connection test successful: {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Marzban connection test failed: {e}")
            return False

    async def create_user(
        self,
        username: str,
        data_limit_gb: Optional[int],
        expire_days: int,
        device_limit: int
    ) -> Dict:
        """ایجاد کاربر جدید"""
        try:
            # محاسبه data_limit به بایت
            data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb else 0

            # محاسبه تاریخ انقضا (timestamp)
            expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp())

            # ایجاد کاربر
            result = await self.api.create_user(
                username=username,
                data_limit=data_limit_bytes,
                expire=expire_timestamp,
                data_limit_reset_strategy="no_reset",
                status="active"
            )

            logger.info(f"Marzban user created: {username}")

            return {
                "panel_id": result.get("id") or result.get("username"),
                "username": result.get("username"),
                "subscription_url": result.get("subscription_url") or result.get("links", [None])[0]
            }

        except Exception as e:
            logger.error(f"Failed to create Marzban user {username}: {e}")
            raise PanelOperationError(f"Failed to create user: {e}")

    async def get_user(self, username: str) -> Dict:
        """دریافت اطلاعات کاربر"""
        try:
            user = await self.api.get_user(username)

            if not user:
                raise PanelUserNotFoundError(f"User {username} not found")

            return {
                "username": user.get("username"),
                "status": user.get("status"),
                "used_traffic": user.get("used_traffic", 0),
                "data_limit": user.get("data_limit", 0),
                "expire": user.get("expire"),
                "subscription_url": user.get("subscription_url")
            }

        except PanelUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get Marzban user {username}: {e}")
            raise PanelOperationError(f"Failed to get user: {e}")

    async def update_user(self, username: str, **kwargs) -> Dict:
        """بروزرسانی کاربر"""
        try:
            result = await self.api.update_user(username, **kwargs)
            logger.info(f"Marzban user updated: {username}")
            return result

        except Exception as e:
            logger.error(f"Failed to update Marzban user {username}: {e}")
            raise PanelOperationError(f"Failed to update user: {e}")

    async def delete_user(self, username: str) -> bool:
        """حذف کاربر"""
        try:
            await self.api.delete_user(username)
            logger.info(f"Marzban user deleted: {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Marzban user {username}: {e}")
            raise PanelOperationError(f"Failed to delete user: {e}")

    async def get_user_usage(self, username: str) -> Dict:
        """دریافت میزان استفاده"""
        user = await self.get_user(username)

        used_bytes = user.get("used_traffic", 0)
        data_limit = user.get("data_limit", 0)
        remaining_bytes = max(0, data_limit - used_bytes) if data_limit > 0 else -1  # -1 = نامحدود

        return {
            "used_bytes": used_bytes,
            "remaining_bytes": remaining_bytes,
            "expire_date": datetime.fromtimestamp(user.get("expire", 0)) if user.get("expire") else None
        }

    async def toggle_user_status(self, username: str, enabled: bool) -> bool:
        """فعال/غیرفعال کردن"""
        try:
            status = "active" if enabled else "disabled"
            await self.update_user(username, status=status)
            logger.info(f"Marzban user {username} status changed to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to toggle Marzban user {username}: {e}")
            return False

    async def extend_user_time(self, username: str, days: int) -> Dict:
        """افزودن زمان"""
        user = await self.get_user(username)
        current_expire = user.get("expire", int(datetime.now().timestamp()))

        # اگر منقضی شده، از الان شروع کن
        if current_expire < int(datetime.now().timestamp()):
            current_expire = int(datetime.now().timestamp())

        new_expire = current_expire + (days * 24 * 3600)

        return await self.update_user(username, expire=new_expire)

    async def add_user_traffic(self, username: str, gb: int) -> Dict:
        """افزودن حجم"""
        user = await self.get_user(username)
        current_limit = user.get("data_limit", 0)

        new_limit = current_limit + (gb * 1024 * 1024 * 1024)

        return await self.update_user(username, data_limit=new_limit)
