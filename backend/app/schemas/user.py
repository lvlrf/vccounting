"""
User Schemas
Pydantic schemas برای validation و serialization
"""
from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime
from decimal import Decimal

from ..models.user import UserRole


# Base Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRole


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID4
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# Reseller Group Schemas
class ResellerGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    discount_percentage: Decimal = Field(default=0, ge=0, le=100)
    default_credit: Decimal = Field(default=0, ge=0)


class ResellerGroupCreate(ResellerGroupBase):
    pass


class ResellerGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    default_credit: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ResellerGroupResponse(ResellerGroupBase):
    id: UUID4
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Reseller Schemas
class ResellerBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    telegram: Optional[str] = Field(None, max_length=50)


class ResellerCreate(UserCreate, ResellerBase):
    group_id: Optional[UUID4] = None


class ResellerUpdate(ResellerBase):
    group_id: Optional[UUID4] = None


class ResellerResponse(ResellerBase):
    id: UUID4
    user_id: UUID4
    group_id: Optional[UUID4]
    total_accounts_created: Decimal
    total_credit_spent: Decimal
    total_credit_purchased: Decimal
    created_at: datetime
    updated_at: datetime

    # Include user info
    user: UserResponse

    class Config:
        from_attributes = True


# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
