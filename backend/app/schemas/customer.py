"""
Customer Schemas
Pydantic schemas برای مشتریان و اشتراک‌ها
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# ========== Customer Schemas ==========

class CustomerBase(BaseModel):
    """Schema پایه مشتری"""
    full_name: str = Field(..., min_length=1, max_length=100, description="نام کامل")
    email: Optional[EmailStr] = Field(None, description="ایمیل")
    phone: str = Field(..., min_length=10, max_length=20, description="شماره تماس")
    telegram_chat_id: Optional[str] = Field(None, max_length=50, description="Telegram Chat ID")
    telegram_username: Optional[str] = Field(None, max_length=50, description="Telegram Username")
    notes: Optional[str] = Field(None, description="یادداشت‌ها")


class CustomerCreate(CustomerBase):
    """Schema ایجاد مشتری"""
    representative_id: Optional[UUID] = Field(None, description="شناسه نماینده معرف")
    password: Optional[str] = Field(None, min_length=6, description="رمز عبور (در صورت نیاز به پنل مشتری)")


class CustomerUpdate(BaseModel):
    """Schema بروزرسانی مشتری"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    telegram_chat_id: Optional[str] = Field(None, max_length=50)
    telegram_username: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema پاسخ مشتری"""
    id: UUID
    representative_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerWithStats(CustomerResponse):
    """Schema مشتری با آمار"""
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    total_accounts: int = 0


# ========== Subscription Schemas ==========

class SubscriptionBase(BaseModel):
    """Schema پایه اشتراک"""
    plan: str = Field(..., description="نوع پلن (basic, pro, enterprise)")
    expires_at: datetime = Field(..., description="تاریخ انقضا")
    auto_renew: bool = Field(False, description="تمدید خودکار")


class SubscriptionCreate(SubscriptionBase):
    """Schema ایجاد اشتراک"""
    customer_id: UUID = Field(..., description="شناسه مشتری")
    starts_at: Optional[datetime] = Field(None, description="تاریخ شروع (پیش‌فرض: الان)")


class SubscriptionUpdate(BaseModel):
    """Schema بروزرسانی اشتراک"""
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None
    auto_renew: Optional[bool] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    """Schema پاسخ اشتراک"""
    id: UUID
    customer_id: UUID
    starts_at: datetime
    created_at: datetime
    is_active: bool

    # محاسبه شده
    is_expired: bool = Field(False, description="آیا منقضی شده؟")
    days_remaining: int = Field(0, description="روزهای باقیمانده")

    model_config = ConfigDict(from_attributes=True)


# ========== List & Pagination ==========

class CustomerListResponse(BaseModel):
    """Schema لیست مشتریان"""
    customers: list[CustomerResponse]
    total: int
    page: int = 1
    page_size: int = 50


class SubscriptionListResponse(BaseModel):
    """Schema لیست اشتراک‌ها"""
    subscriptions: list[SubscriptionResponse]
    total: int
    page: int = 1
    page_size: int = 50
