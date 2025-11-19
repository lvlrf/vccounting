"""
Customer Models
مدل‌های مشتریان نهایی و اشتراک‌ها
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..database import Base


class SubscriptionPlan(str, enum.Enum):
    """پلن‌های اشتراک"""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Customer(Base):
    """
    مشتریان نهایی سیستم (کاربران اصلی)
    این افراد از سرویس‌ها استفاده می‌کنند
    """
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # اطلاعات شناسایی
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=False, index=True)

    # امنیت (در صورت نیاز به پنل مشتری)
    password_hash = Column(String(255), nullable=True)

    # اطلاعات تلگرام (برای نوتیف‌ها)
    telegram_chat_id = Column(String(50), nullable=True)
    telegram_username = Column(String(50), nullable=True)

    # نماینده معرف
    representative_id = Column(UUID(as_uuid=True), ForeignKey("resellers.id"), nullable=True)

    # یادداشت‌ها
    notes = Column(Text, nullable=True)

    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)

    # زمان
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    representative = relationship("Reseller", back_populates="customers")
    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    accounts = relationship("CustomerAccount", back_populates="customer")

    def __repr__(self):
        return f"<Customer(full_name='{self.full_name}', phone='{self.phone}')>"


class Subscription(Base):
    """
    اشتراک‌های مشتریان
    برای مدیریت دسترسی و زمان انقضای سرویس‌ها
    """
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)

    # پلن اشتراک
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False)

    # زمان
    starts_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # تمدید خودکار
    auto_renew = Column(Boolean, default=False, nullable=False)

    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(customer_id='{self.customer_id}', plan='{self.plan}')>"

    @property
    def is_expired(self):
        """بررسی انقضای اشتراک"""
        return datetime.utcnow() > self.expires_at

    @property
    def days_remaining(self):
        """روزهای باقی‌مانده تا انقضا"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return delta.days
