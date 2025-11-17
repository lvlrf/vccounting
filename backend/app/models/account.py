"""
Customer Account Models
مدل اکانت‌های مشتریان
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Integer, Numeric, Text, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..database import Base


class AccountStatus(str, enum.Enum):
    """وضعیت اکانت"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    DELETED = "deleted"
    SUSPENDED = "suspended"


class CustomerAccount(Base):
    """
    اکانت‌های مشتریان
    """
    __tablename__ = "customer_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reseller_id = Column(UUID(as_uuid=True), ForeignKey("resellers.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    service_plan_id = Column(UUID(as_uuid=True), ForeignKey("service_plans.id"), nullable=False)

    # اطلاعات اکانت
    username = Column(String(100), nullable=False, index=True)
    panel_account_id = Column(String(255), nullable=True)  # ID در پنل مقصد
    subscription_url = Column(Text, nullable=True)  # لینک اشتراک

    # اطلاعات مشتری (اختیاری)
    customer_name = Column(String(100), nullable=True)
    customer_note = Column(Text, nullable=True)

    # مشخصات سرویس
    data_limit_gb = Column(Integer, nullable=True)  # null = نامحدود
    data_used_bytes = Column(BigInteger, default=0, nullable=False)
    expire_date = Column(DateTime, nullable=False, index=True)
    device_limit = Column(Integer, default=1, nullable=False)

    # وضعیت
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False, index=True)

    # کریدیت
    credit_cost = Column(Numeric(10, 2), nullable=False)  # هزینه اولیه

    # اطلاعات sync
    last_synced = Column(DateTime, nullable=True)
    sync_data = Column(JSON, nullable=True)  # آخرین داده از پنل

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    reseller = relationship("Reseller", back_populates="accounts")
    product = relationship("Product")
    service_plan = relationship("ServicePlan", back_populates="accounts")
    sync_logs = relationship("AccountSyncLog", back_populates="account")

    def __repr__(self):
        return f"<CustomerAccount(username='{self.username}', status='{self.status}')>"

    @property
    def data_used_gb(self):
        """محاسبه حجم استفاده شده به GB"""
        return self.data_used_bytes / (1024 ** 3) if self.data_used_bytes else 0

    @property
    def data_remaining_gb(self):
        """محاسبه حجم باقیمانده"""
        if self.data_limit_gb is None:
            return None  # نامحدود
        return max(0, self.data_limit_gb - self.data_used_gb)

    @property
    def is_expired(self):
        """آیا منقضی شده است؟"""
        return datetime.utcnow() > self.expire_date

    @property
    def days_remaining(self):
        """تعداد روزهای باقیمانده"""
        delta = self.expire_date - datetime.utcnow()
        return max(0, delta.days)


class AccountSyncLog(Base):
    """
    لاگ همگام‌سازی اکانت‌ها
    برای رصد تغییرات و مشکلات sync
    """
    __tablename__ = "account_sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("customer_accounts.id"), nullable=False, index=True)

    sync_type = Column(String(50), nullable=False)  # "auto", "manual", "create", "update", "delete"
    status = Column(String(20), nullable=False)  # "success", "failed"
    message = Column(Text, nullable=True)

    # داده‌های sync شده
    synced_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    account = relationship("CustomerAccount", back_populates="sync_logs")

    def __repr__(self):
        return f"<AccountSyncLog(account_id='{self.account_id}', status='{self.status}')>"
