"""
Base Panel Integration
کلاس پایه برای اتصال به پنل‌ها
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BasePanelIntegration(ABC):
    """
    کلاس پایه برای اتصال به پنل‌های مختلف
    هر پنل جدید باید این interface را پیاده‌سازی کند
    """

    def __init__(self, base_url: str, username: str, password: str):
        """
        Args:
            base_url: آدرس پایه API پنل
            username: نام کاربری
            password: رمز عبور
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        تست اتصال به پنل

        Returns:
            bool: True اگر اتصال موفق باشد
        """
        pass

    @abstractmethod
    async def create_user(
        self,
        username: str,
        data_limit_gb: Optional[int],
        expire_days: int,
        device_limit: int
    ) -> Dict:
        """
        ایجاد کاربر جدید در پنل

        Args:
            username: نام کاربری
            data_limit_gb: محدودیت حجم به گیگابایت (None = نامحدود)
            expire_days: تعداد روزهای اعتبار
            device_limit: محدودیت تعداد دستگاه

        Returns:
            Dict با کلیدهای:
                - panel_id: شناسه کاربر در پنل
                - username: نام کاربری
                - subscription_url: لینک اشتراک
        """
        pass

    @abstractmethod
    async def get_user(self, username: str) -> Dict:
        """
        دریافت اطلاعات کاربر

        Args:
            username: نام کاربری

        Returns:
            Dict با اطلاعات کاربر
        """
        pass

    @abstractmethod
    async def update_user(
        self,
        username: str,
        **kwargs
    ) -> Dict:
        """
        بروزرسانی اطلاعات کاربر

        Args:
            username: نام کاربری
            **kwargs: فیلدهای قابل بروزرسانی

        Returns:
            Dict با اطلاعات بروز شده
        """
        pass

    @abstractmethod
    async def delete_user(self, username: str) -> bool:
        """
        حذف کاربر

        Args:
            username: نام کاربری

        Returns:
            bool: True اگر موفق باشد
        """
        pass

    @abstractmethod
    async def get_user_usage(self, username: str) -> Dict:
        """
        دریافت میزان استفاده کاربر

        Args:
            username: نام کاربری

        Returns:
            Dict با کلیدهای:
                - used_bytes: حجم استفاده شده (بایت)
                - remaining_bytes: حجم باقیمانده (بایت)
                - expire_date: تاریخ انقضا
        """
        pass

    @abstractmethod
    async def toggle_user_status(self, username: str, enabled: bool) -> bool:
        """
        فعال/غیرفعال کردن کاربر

        Args:
            username: نام کاربری
            enabled: True = فعال، False = غیرفعال

        Returns:
            bool: True اگر موفق باشد
        """
        pass

    async def extend_user_time(self, username: str, days: int) -> Dict:
        """
        افزودن زمان به اکانت (پیاده‌سازی پیش‌فرض)

        Args:
            username: نام کاربری
            days: تعداد روز

        Returns:
            Dict با اطلاعات بروز شده
        """
        user = await self.get_user(username)
        # پیاده‌سازی در کلاس‌های فرزند
        return user

    async def add_user_traffic(self, username: str, gb: int) -> Dict:
        """
        افزودن حجم به اکانت (پیاده‌سازی پیش‌فرض)

        Args:
            username: نام کاربری
            gb: حجم به گیگابایت

        Returns:
            Dict با اطلاعات بروز شده
        """
        user = await self.get_user(username)
        # پیاده‌سازی در کلاس‌های فرزند
        return user

    async def reset_user_traffic(self, username: str) -> Dict:
        """
        ریست ترافیک کاربر

        Args:
            username: نام کاربری

        Returns:
            Dict با اطلاعات بروز شده
        """
        return await self.update_user(username, used_traffic=0)


class PanelConnectionError(Exception):
    """خطای اتصال به پنل"""
    pass


class PanelUserNotFoundError(Exception):
    """کاربر در پنل یافت نشد"""
    pass


class PanelOperationError(Exception):
    """خطای عملیات پنل"""
    pass
