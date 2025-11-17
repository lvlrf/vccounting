"""
Credit Schemas
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from decimal import Decimal

from ..models.credit import TransactionType, OperationType


# Credit Balance Schemas
class CreditBalanceResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    balance: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True


# Credit Transaction Schemas
class CreditTransactionBase(BaseModel):
    type: TransactionType
    operation: Optional[OperationType] = None
    amount: Decimal
    description: Optional[str] = None


class CreditTransactionResponse(CreditTransactionBase):
    id: UUID4
    reseller_id: UUID4
    balance_before: Decimal
    balance_after: Decimal
    related_account_id: Optional[UUID4]
    related_product_id: Optional[UUID4]
    admin_note: Optional[str]
    created_by: Optional[UUID4]
    created_at: datetime

    class Config:
        from_attributes = True


# Manual Credit Operations (Admin only)
class ManualCreditAdd(BaseModel):
    reseller_id: UUID4
    amount: Decimal = Field(..., gt=0)
    admin_note: Optional[str] = None


class ManualCreditDeduct(BaseModel):
    reseller_id: UUID4
    amount: Decimal = Field(..., gt=0)
    admin_note: Optional[str] = None


# Credit Pricing Schemas
class CreditPricingBase(BaseModel):
    product_group_id: UUID4
    operation_type: OperationType
    service_plan_id: Optional[UUID4] = None
    credit_amount: Decimal = Field(..., ge=0)
    applies_to_reseller_group_id: Optional[UUID4] = None


class CreditPricingCreate(CreditPricingBase):
    pass


class CreditPricingUpdate(BaseModel):
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CreditPricingResponse(CreditPricingBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
