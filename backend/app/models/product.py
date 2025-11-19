"""
Product Models
مدل‌های محصولات و پلن‌های سرویس
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..database import Base


class ProductType(str, enum.Enum):
    """نوع محصول"""
    VPN_PANEL = "vpn_panel"
    HOSTING = "hosting"
    DOMAIN = "domain"
    OTHER = "other"


class IntegrationType(str, enum.Enum):
    """نوع اتصال به محصول"""
    API = "api"  # اتصال API خودکار
    MANUAL = "manual"  # دستی
    SEMI_AUTO = "semi_auto"  # نیمه خودکار


class PanelType(str, enum.Enum):
    """نوع پنل (برای محصولات VPN) - پشتیبانی از OpexCore"""
    MARZBAN = "marzban"
    REMNAWAVE = "remnawave"
    MARZNESHIN = "marzneshin"
    OVPANEL = "ovpanel"


class Product(Base):
    """
    محصولات قابل فروش
    """
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    product_type = Column(SQLEnum(ProductType), nullable=False)
    category = Column(String(50), nullable=False)  # vpn, web, other
    integration_type = Column(SQLEnum(IntegrationType), nullable=False)

    # برای محصولات با پنل
    panel_type = Column(SQLEnum(PanelType), nullable=True)
    requires_panel_connection = Column(Boolean, default=False, nullable=False)

    # تنظیمات API (در صورت وجود)
    api_config = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service_plans = relationship("ServicePlan", back_populates="product")
    group_items = relationship("ProductGroupItem", back_populates="product")
    panel_connections = relationship("PanelConnection", back_populates="product")

    def __repr__(self):
        return f"<Product(name='{self.name}', type='{self.product_type}')>"


class ProductGroup(Base):
    """
    گروه‌بندی محصولات
    مثال: "VPN پریمیوم", "VPN اقتصادی"
    با قابلیت تخصیص به گروه‌های مشتریان و اعمال تخفیف
    """
    __tablename__ = "product_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # تخفیف‌های گروهی
    reseller_discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)  # تخفیف برای نماینده
    customer_discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)  # تخفیف برای مشتری

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    products = relationship("ProductGroupItem", back_populates="group")
    pricing_rules = relationship("CreditPricing", back_populates="product_group")

    def __repr__(self):
        return f"<ProductGroup(name='{self.name}')>"


class ProductGroupItem(Base):
    """
    محصولات داخل هر گروه
    رابطه many-to-many بین Product و ProductGroup
    """
    __tablename__ = "product_group_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("product_groups.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="group_items")
    group = relationship("ProductGroup", back_populates="products")

    def __repr__(self):
        return f"<ProductGroupItem(product_id='{self.product_id}', group_id='{self.group_id}')>"


class PlanType(str, enum.Enum):
    """نوع پلن"""
    DAILY = "daily"
    MONTHLY = "monthly"
    VOLUME = "volume"
    UNLIMITED = "unlimited"
    CUSTOM = "custom"


class ServicePlan(Base):
    """
    پلن‌های سرویس برای هر محصول
    مثال: "ماهانه 100GB", "روزانه 2GB"
    """
    __tablename__ = "service_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    name = Column(String(100), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)

    # مشخصات فنی (برای VPN)
    data_limit_gb = Column(Integer, nullable=True)  # null = نامحدود
    duration_days = Column(Integer, nullable=False)
    device_limit = Column(Integer, default=1, nullable=False)

    # قیمت پایه
    credit_cost = Column(Numeric(10, 2), nullable=False)

    # سایر پارامترها (برای قابلیت توسعه)
    custom_params = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="service_plans")
    accounts = relationship("CustomerAccount", back_populates="service_plan")

    def __repr__(self):
        return f"<ServicePlan(name='{self.name}', cost={self.credit_cost})>"
