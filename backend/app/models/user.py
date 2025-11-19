"""
User Models
مدل‌های کاربری سیستم (Admin, Reseller)
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..database import Base


# جدول واسط برای رابطه Many-to-Many بین Reseller و ResellerGroup
reseller_group_association = Table(
    'reseller_group_memberships',
    Base.metadata,
    Column('reseller_id', UUID(as_uuid=True), ForeignKey('resellers.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', UUID(as_uuid=True), ForeignKey('reseller_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow, nullable=False)
)


class UserRole(str, enum.Enum):
    """نقش‌های کاربری"""
    ADMIN = "admin"
    RESELLER = "reseller"


class User(Base):
    """
    کاربران سیستم (Admin و Reseller)
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    role = Column(SQLEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    reseller_profile = relationship("Reseller", back_populates="user", uselist=False)
    credit_balance = relationship("CreditBalance", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


class ResellerGroup(Base):
    """
    گروه‌های نمایندگی
    برای دسته‌بندی نمایندگان و اعمال تخفیف/محدودیت گروهی
    یک نماینده می‌تواند عضو چندین گروه باشد
    """
    __tablename__ = "reseller_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)

    # تخفیف و ویژگی‌های گروه
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)  # 0-100
    default_credit = Column(Numeric(10, 2), default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships - Many-to-Many با Reseller
    resellers = relationship(
        "Reseller",
        secondary=reseller_group_association,
        back_populates="groups"
    )

    def __repr__(self):
        return f"<ResellerGroup(name='{self.name}')>"


class Reseller(Base):
    """
    اطلاعات تکمیلی نمایندگان
    یک نماینده می‌تواند عضو چندین گروه باشد
    """
    __tablename__ = "resellers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # اطلاعات تماس
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    telegram = Column(String(50), nullable=True)

    # کد معرف اختصاصی
    referral_code = Column(String(20), unique=True, nullable=True, index=True)

    # آمار
    total_accounts_created = Column(Numeric, default=0, nullable=False)
    total_credit_spent = Column(Numeric(10, 2), default=0, nullable=False)
    total_credit_purchased = Column(Numeric(10, 2), default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reseller_profile")

    # Many-to-Many با ResellerGroup
    groups = relationship(
        "ResellerGroup",
        secondary=reseller_group_association,
        back_populates="resellers"
    )

    product_accesses = relationship("ResellerProductAccess", back_populates="reseller")
    accounts = relationship("CustomerAccount", back_populates="reseller")
    customers = relationship("Customer", back_populates="representative")

    def __repr__(self):
        return f"<Reseller(user_id='{self.user_id}', full_name='{self.full_name}')>"
