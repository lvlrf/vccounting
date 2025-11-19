"""
Panel Integration Factory
Factory pattern برای ایجاد integration مناسب بر اساس نوع پنل
"""
from typing import Dict
import logging

from .base import BasePanelIntegration, PanelConnectionError
from .marzban import MarzbanIntegration
from .remnawave import RemnawaveIntegration
from .marzneshin import MarzneshinIntegration
from .ovpanel import OvPanelIntegration

logger = logging.getLogger(__name__)


class PanelIntegrationFactory:
    """
    Factory برای ایجاد integration مناسب
    پشتیبانی از: Marzban, Remnawave, Marzneshin, OvPanel (via OpexCore)
    """

    # نگاشت نوع پنل به کلاس integration
    INTEGRATIONS = {
        "marzban": MarzbanIntegration,
        "remnawave": RemnawaveIntegration,
        "marzneshin": MarzneshinIntegration,
        "ovpanel": OvPanelIntegration,
    }

    @classmethod
    def create(cls, panel_type: str, connection_config: Dict) -> BasePanelIntegration:
        """
        ایجاد integration مناسب

        Args:
            panel_type: نوع پنل (marzban, remnawave, marzneshin)
            connection_config: تنظیمات اتصال با کلیدهای:
                - base_url
                - username
                - password

        Returns:
            BasePanelIntegration: instance مناسب

        Raises:
            ValueError: اگر نوع پنل پشتیبانی نشود
            PanelConnectionError: اگر خطا در ایجاد رخ دهد
        """
        panel_type = panel_type.lower()

        if panel_type not in cls.INTEGRATIONS:
            supported = ", ".join(cls.INTEGRATIONS.keys())
            raise ValueError(
                f"Panel type '{panel_type}' is not supported. "
                f"Supported types: {supported}"
            )

        integration_class = cls.INTEGRATIONS[panel_type]

        try:
            integration = integration_class(
                base_url=connection_config["base_url"],
                username=connection_config["username"],
                password=connection_config["password"]
            )

            logger.info(f"Created {panel_type} integration for {connection_config['base_url']}")
            return integration

        except KeyError as e:
            raise PanelConnectionError(f"Missing required config key: {e}")
        except Exception as e:
            logger.error(f"Failed to create {panel_type} integration: {e}")
            raise PanelConnectionError(f"Failed to create integration: {e}")

    @classmethod
    def get_supported_panels(cls) -> list:
        """
        دریافت لیست پنل‌های پشتیبانی شده

        Returns:
            list: لیست نام پنل‌ها
        """
        return list(cls.INTEGRATIONS.keys())

    @classmethod
    def register_panel(cls, panel_type: str, integration_class: type):
        """
        ثبت پنل جدید (برای قابلیت توسعه)

        Args:
            panel_type: نوع پنل
            integration_class: کلاس integration

        Example:
            PanelIntegrationFactory.register_panel("new_panel", NewPanelIntegration)
        """
        if not issubclass(integration_class, BasePanelIntegration):
            raise ValueError(
                f"{integration_class.__name__} must inherit from BasePanelIntegration"
            )

        cls.INTEGRATIONS[panel_type.lower()] = integration_class
        logger.info(f"Registered new panel type: {panel_type}")
