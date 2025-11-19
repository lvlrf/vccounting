"""
OvPanel Integration using OpexCore
اتصال به OvPanel با استفاده از کتابخانه OpexCore
"""
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

try:
    from opexcore import OvPanel as OpexOvPanel
except ImportError:
    OpexOvPanel = None

from .base import (
    BasePanelIntegration,
    PanelConnectionError,
    PanelUserNotFoundError,
    PanelOperationError
)

logger = logging.getLogger(__name__)


class OvPanelIntegration(BasePanelIntegration):
    """
    اتصال به OvPanel با استفاده از OpexCore

    OpexCore Documentation:
    https://github.com/opexcore/opexcore
    """

    def __init__(self, base_url: str, username: str, password: str):
        super().__init__(base_url, username, password)

        if OpexOvPanel is None:
            raise ImportError(
                "OpexCore library is not installed. "
                "Install it with: pip install opexcore"
            )

        try:
            self.client = OpexOvPanel(
                base_url=self.base_url,
                username=self.username,
                password=self.password
            )
        except Exception as e:
            logger.error(f"Failed to initialize OvPanel client: {e}")
            raise PanelConnectionError(f"Cannot connect to OvPanel: {e}")

    async def test_connection(self) -> bool:
        """تست اتصال به پنل"""
        try:
            # تست اتصال با دریافت لیست کاربران یا admin info
            result = await self.client.get_admin_info()
            return result is not None
        except Exception as e:
            logger.error(f"OvPanel connection test failed: {e}")
            return False

    async def create_user(
        self,
        username: str,
        data_limit_gb: Optional[int],
        expire_days: int,
        device_limit: int
    ) -> Dict:
        """ایجاد کاربر جدید در OvPanel"""
        try:
            # محاسبه تاریخ انقضا
            expire_date = datetime.utcnow() + timedelta(days=expire_days)

            # تبدیل GB به bytes (اگر محدود باشد)
            data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb else 0

            # ایجاد کاربر با OpexCore
            result = await self.client.add_user(
                username=username,
                data_limit=data_limit_bytes,
                expire=int(expire_date.timestamp()),
                connection_limit=device_limit
            )

            if not result or not result.get('success'):
                raise PanelOperationError(f"Failed to create user: {result}")

            return {
                'panel_id': result.get('user_id') or username,
                'username': username,
                'subscription_url': result.get('subscription_url', '')
            }

        except Exception as e:
            logger.error(f"Error creating user in OvPanel: {e}")
            raise PanelOperationError(f"Cannot create user: {e}")

    async def get_user(self, username: str) -> Dict:
        """دریافت اطلاعات کاربر"""
        try:
            user = await self.client.get_user(username=username)

            if not user:
                raise PanelUserNotFoundError(f"User '{username}' not found")

            return {
                'username': user.get('username'),
                'data_limit_bytes': user.get('data_limit', 0),
                'data_used_bytes': user.get('used_traffic', 0),
                'expire_timestamp': user.get('expire', 0),
                'connection_limit': user.get('connection_limit', 1),
                'is_active': user.get('status') == 'active',
                'subscription_url': user.get('subscription_url', '')
            }

        except PanelUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting user from OvPanel: {e}")
            raise PanelOperationError(f"Cannot get user: {e}")

    async def update_user(self, username: str, **kwargs) -> Dict:
        """بروزرسانی اطلاعات کاربر"""
        try:
            # تبدیل فیلدها به فرمت OvPanel
            update_data = {}

            if 'data_limit_gb' in kwargs:
                gb = kwargs['data_limit_gb']
                update_data['data_limit'] = gb * 1024 * 1024 * 1024 if gb else 0

            if 'expire_days' in kwargs:
                expire_date = datetime.utcnow() + timedelta(days=kwargs['expire_days'])
                update_data['expire'] = int(expire_date.timestamp())

            if 'connection_limit' in kwargs:
                update_data['connection_limit'] = kwargs['connection_limit']

            if 'is_active' in kwargs:
                update_data['status'] = 'active' if kwargs['is_active'] else 'disabled'

            result = await self.client.modify_user(
                username=username,
                **update_data
            )

            if not result or not result.get('success'):
                raise PanelOperationError(f"Failed to update user: {result}")

            return await self.get_user(username)

        except Exception as e:
            logger.error(f"Error updating user in OvPanel: {e}")
            raise PanelOperationError(f"Cannot update user: {e}")

    async def delete_user(self, username: str) -> bool:
        """حذف کاربر"""
        try:
            result = await self.client.remove_user(username=username)
            return result and result.get('success', False)
        except Exception as e:
            logger.error(f"Error deleting user from OvPanel: {e}")
            raise PanelOperationError(f"Cannot delete user: {e}")

    async def get_user_usage(self, username: str) -> Dict:
        """دریافت میزان استفاده کاربر"""
        try:
            user = await self.get_user(username)

            used_bytes = user.get('data_used_bytes', 0)
            limit_bytes = user.get('data_limit_bytes', 0)
            remaining_bytes = max(0, limit_bytes - used_bytes) if limit_bytes else None

            return {
                'used_bytes': used_bytes,
                'remaining_bytes': remaining_bytes,
                'expire_timestamp': user.get('expire_timestamp', 0)
            }

        except Exception as e:
            logger.error(f"Error getting user usage from OvPanel: {e}")
            raise PanelOperationError(f"Cannot get user usage: {e}")

    async def toggle_user_status(self, username: str, enabled: bool) -> bool:
        """فعال/غیرفعال کردن کاربر"""
        try:
            result = await self.client.modify_user(
                username=username,
                status='active' if enabled else 'disabled'
            )
            return result and result.get('success', False)
        except Exception as e:
            logger.error(f"Error toggling user status in OvPanel: {e}")
            raise PanelOperationError(f"Cannot toggle user status: {e}")

    async def extend_user_time(self, username: str, days: int) -> Dict:
        """افزودن زمان به اکانت"""
        try:
            user = await self.get_user(username)
            current_expire = user.get('expire_timestamp', int(datetime.utcnow().timestamp()))

            # اگر منقضی شده، از الان شروع کن
            if current_expire < int(datetime.utcnow().timestamp()):
                new_expire = datetime.utcnow() + timedelta(days=days)
            else:
                new_expire = datetime.fromtimestamp(current_expire) + timedelta(days=days)

            return await self.update_user(
                username=username,
                expire_timestamp=int(new_expire.timestamp())
            )

        except Exception as e:
            logger.error(f"Error extending user time in OvPanel: {e}")
            raise PanelOperationError(f"Cannot extend user time: {e}")

    async def add_user_traffic(self, username: str, gb: int) -> Dict:
        """افزودن حجم به اکانت"""
        try:
            user = await self.get_user(username)
            current_limit = user.get('data_limit_bytes', 0)
            additional_bytes = gb * 1024 * 1024 * 1024
            new_limit = current_limit + additional_bytes

            return await self.update_user(
                username=username,
                data_limit=new_limit
            )

        except Exception as e:
            logger.error(f"Error adding traffic to user in OvPanel: {e}")
            raise PanelOperationError(f"Cannot add traffic: {e}")
