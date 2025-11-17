"""
Panel Connection Models
مدل اتصالات به پنل‌های مختلف
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class PanelConnection(Base):
    """
    اتصالات به پنل‌های مختلف
    """
    __tablename__ = "panel_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    reseller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # null = اتصال مشترک

    name = Column(String(100), nullable=False)  # نام توصیفی برای اتصال
    panel_type = Column(String(50), nullable=False)  # "marzban", "remnawave", "marzneshin"

    base_url = Column(String(255), nullable=False)
    credentials = Column(Text, nullable=False)  # JSON رمزگذاری شده {username, password}

    # تنظیمات
    is_shared = Column(Boolean, default=False, nullable=False)  # آیا چند نماینده می‌توانند استفاده کنند؟
    is_active = Column(Boolean, default=True, nullable=False)

    # وضعیت اتصال
    last_tested = Column(DateTime, nullable=True)
    last_test_status = Column(String(20), nullable=True)  # "success", "failed"
    last_test_message = Column(Text, nullable=True)

    # آمار
    total_accounts = Column(Numeric, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="panel_connections")
    reseller = relationship("User")
    product_accesses = relationship("ResellerProductAccess", back_populates="panel_connection")

    def __repr__(self):
        return f"<PanelConnection(name='{self.name}', panel_type='{self.panel_type}', is_shared={self.is_shared})>"


class ResellerProductAccess(Base):
    """
    دسترسی نماینده به محصولات
    مشخص می‌کند که کدام نماینده به کدام محصول دسترسی دارد
    """
    __tablename__ = "reseller_product_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reseller_id = Column(UUID(as_uuid=True), ForeignKey("resellers.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_group_id = Column(UUID(as_uuid=True), ForeignKey("product_groups.id"), nullable=False)

    # اتصال به پنل
    panel_connection_id = Column(UUID(as_uuid=True), ForeignKey("panel_connections.id"), nullable=True)

    # محدودیت‌ها
    max_accounts = Column(Numeric, nullable=True)  # null = نامحدود
    current_accounts = Column(Numeric, default=0, nullable=False)

    # قیمت‌گذاری سفارشی (اختیاری)
    custom_pricing = Column(JSON, nullable=True)  # {operation_type: credit_amount}

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reseller = relationship("Reseller", back_populates="product_accesses")
    product = relationship("Product")
    product_group = relationship("ProductGroup")
    panel_connection = relationship("PanelConnection", back_populates="product_accesses")

    def __repr__(self):
        return f"<ResellerProductAccess(reseller_id='{self.reseller_id}', product_id='{self.product_id}')>"


# Fix imports
from sqlalchemy import Numeric, Boolean
