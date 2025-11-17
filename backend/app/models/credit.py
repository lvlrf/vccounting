"""
Credit Models
مدل‌های سیستم کریدیت و قیمت‌گذاری
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..database import Base


class CreditBalance(Base):
    """
    موجودی کریدیت هر کاربر
    """
    __tablename__ = "credit_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    balance = Column(Numeric(10, 2), default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="credit_balance")

    def __repr__(self):
        return f"<CreditBalance(user_id='{self.user_id}', balance={self.balance})>"


class TransactionType(str, enum.Enum):
    """نوع تراکنش"""
    PURCHASE = "purchase"  # خرید (کسر کریدیت)
    REFUND = "refund"  # برگشت کریدیت
    MANUAL_ADD = "manual_add"  # شارژ دستی توسط ادمین
    MANUAL_DEDUCT = "manual_deduct"  # کسر دستی توسط ادمین


class OperationType(str, enum.Enum):
    """نوع عملیات روی اکانت"""
    CREATE_ACCOUNT = "create_account"
    RENEW = "renew"
    ADD_TRAFFIC = "add_traffic"
    EXTEND = "extend"
    DELETE = "delete"
    TOGGLE_STATUS = "toggle_status"
    RESET_TRAFFIC = "reset_traffic"
    MANUAL = "manual"  # تراکنش دستی


class CreditTransaction(Base):
    """
    تراکنش‌های کریدیت
    """
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reseller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    type = Column(SQLEnum(TransactionType), nullable=False)
    operation = Column(SQLEnum(OperationType), nullable=True)

    amount = Column(Numeric(10, 2), nullable=False)  # مثبت = افزایش، منفی = کاهش
    balance_before = Column(Numeric(10, 2), nullable=False)
    balance_after = Column(Numeric(10, 2), nullable=False)

    # ارجاعات
    related_account_id = Column(UUID(as_uuid=True), ForeignKey("customer_accounts.id"), nullable=True)
    related_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)

    description = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)  # یادداشت ادمین برای تراکنش‌های دستی

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # admin که شارژ کرده
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    reseller = relationship("User", foreign_keys=[reseller_id])
    creator = relationship("User", foreign_keys=[created_by])
    related_account = relationship("CustomerAccount", foreign_keys=[related_account_id])

    def __repr__(self):
        return f"<CreditTransaction(reseller_id='{self.reseller_id}', amount={self.amount}, type='{self.type}')>"


class CreditPricing(Base):
    """
    قیمت‌گذاری عملیات
    قیمت کریدیت برای هر عملیات روی محصولات
    """
    __tablename__ = "credit_pricing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_group_id = Column(UUID(as_uuid=True), ForeignKey("product_groups.id"), nullable=False)
    operation_type = Column(SQLEnum(OperationType), nullable=False)
    service_plan_id = Column(UUID(as_uuid=True), ForeignKey("service_plans.id"), nullable=True)  # null = برای همه پلن‌ها

    credit_amount = Column(Numeric(10, 2), nullable=False)

    # شرایط خاص
    applies_to_reseller_group_id = Column(UUID(as_uuid=True), ForeignKey("reseller_groups.id"), nullable=True)  # null = برای همه

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product_group = relationship("ProductGroup", back_populates="pricing_rules")
    service_plan = relationship("ServicePlan")
    reseller_group = relationship("ResellerGroup")

    def __repr__(self):
        return f"<CreditPricing(operation='{self.operation_type}', amount={self.credit_amount})>"


# این import را در انتها قرار می‌دهیم تا از circular import جلوگیری کنیم
from sqlalchemy import Boolean
