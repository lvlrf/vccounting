"""
Account Schemas
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..models.account import AccountStatus


# Customer Account Schemas
class CustomerAccountBase(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_note: Optional[str] = None


class CustomerAccountCreate(CustomerAccountBase):
    product_id: UUID4
    service_plan_id: UUID4
    username: Optional[str] = Field(None, max_length=100)  # اگر None باشد، خودکار تولید می‌شود


class CustomerAccountUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_note: Optional[str] = None
    status: Optional[AccountStatus] = None


class CustomerAccountResponse(CustomerAccountBase):
    id: UUID4
    reseller_id: UUID4
    product_id: UUID4
    service_plan_id: UUID4
    username: str
    panel_account_id: Optional[str]
    subscription_url: Optional[str]
    data_limit_gb: Optional[int]
    data_used_bytes: int
    expire_date: datetime
    device_limit: int
    status: AccountStatus
    credit_cost: Decimal
    last_synced: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Computed properties
    data_used_gb: float
    data_remaining_gb: Optional[float]
    is_expired: bool
    days_remaining: int

    class Config:
        from_attributes = True


# Account Operations
class RenewAccountRequest(BaseModel):
    days: int = Field(..., gt=0)


class AddTrafficRequest(BaseModel):
    gb: int = Field(..., gt=0)


class ToggleStatusRequest(BaseModel):
    enabled: bool


# Sync Log Schemas
class AccountSyncLogResponse(BaseModel):
    id: UUID4
    account_id: UUID4
    sync_type: str
    status: str
    message: Optional[str]
    synced_data: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
