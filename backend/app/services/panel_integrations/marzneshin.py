"""
Marzneshin Panel Integration
اتصال به Marzneshin Panel با استفاده از OpexCore
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

from .base import BasePanelIntegration, PanelConnectionError, PanelUserNotFoundError, PanelOperationError

logger = logging.getLogger(__name__)


class MarzneshinIntegration(BasePanelIntegration):
    """
    پیاده‌سازی اتصال به Marzneshin Panel
    """

    def __init__(self, base_url: str, username: str, password: str):
        super().__init__(base_url, username, password)
        self.api = None
        self._init_api()

    def _init_api(self):
        """راه‌اندازی API client"""
        try:
            from opexcore import MarzneshinAPI

            self.api = MarzneshinAPI(
                base_url=self.base_url,
                username=self.username,
                password=self.password
            )
            logger.info(f"Marzneshin API initialized for {self.base_url}")
        except ImportError:
            logger.error("OpexCore not installed")
            raise PanelConnectionError("OpexCore library not found")
        except Exception as e:
            logger.error(f"Failed to initialize Marzneshin API: {e}")
            raise PanelConnectionError(f"Failed to initialize API: {e}")

    async def test_connection(self) -> bool:
        """تست اتصال"""
        try:
            await self.api.get_system_stats()
            logger.info(f"Marzneshin connection test successful: {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Marzneshin connection test failed: {e}")
            return False

    async def create_user(
        self,
        username: str,
        data_limit_gb: Optional[int],
        expire_days: int,
        device_limit: int
    ) -> Dict:
        """ایجاد کاربر"""
        try:
            data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb else 0
            expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp())

            result = await self.api.create_user(
                username=username,
                data_limit=data_limit_bytes,
                expire=expire_timestamp,
                status="active"
            )

            logger.info(f"Marzneshin user created: {username}")

            return {
                "panel_id": result.get("id") or result.get("username"),
                "username": result.get("username"),
                "subscription_url": result.get("subscription_url")
            }

        except Exception as e:
            logger.error(f"Failed to create Marzneshin user {username}: {e}")
            raise PanelOperationError(f"Failed to create user: {e}")

    async def get_user(self, username: str) -> Dict:
        """دریافت اطلاعات کاربر"""
        try:
            user = await self.api.get_user(username)
            if not user:
                raise PanelUserNotFoundError(f"User {username} not found")
            return user
        except PanelUserNotFoundError:
            raise
        except Exception as e:
            raise PanelOperationError(f"Failed to get user: {e}")

    async def update_user(self, username: str, **kwargs) -> Dict:
        """بروزرسانی کاربر"""
        try:
            return await self.api.update_user(username, **kwargs)
        except Exception as e:
            raise PanelOperationError(f"Failed to update user: {e}")

    async def delete_user(self, username: str) -> bool:
        """حذف کاربر"""
        try:
            await self.api.delete_user(username)
            return True
        except Exception as e:
            raise PanelOperationError(f"Failed to delete user: {e}")

    async def get_user_usage(self, username: str) -> Dict:
        """دریافت میزان استفاده"""
        user = await self.get_user(username)
        used_bytes = user.get("used_traffic", 0)
        data_limit = user.get("data_limit", 0)
        remaining_bytes = max(0, data_limit - used_bytes) if data_limit > 0 else -1

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
            return True
        except Exception as e:
            logger.error(f"Failed to toggle user {username}: {e}")
            return False
