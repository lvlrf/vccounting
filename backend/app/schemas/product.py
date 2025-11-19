"""
Product Schemas
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..models.product import ProductType, IntegrationType, PanelType, PlanType


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    product_type: ProductType
    category: str = Field(..., max_length=50)
    integration_type: IntegrationType
    panel_type: Optional[PanelType] = None
    requires_panel_connection: bool = False
    api_config: Optional[Dict[str, Any]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    api_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Product Group Schemas
class ProductGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    reseller_discount_percentage: Decimal = Field(default=0, ge=0, le=100, description="تخفیف نماینده")
    customer_discount_percentage: Decimal = Field(default=0, ge=0, le=100, description="تخفیف مشتری")


class ProductGroupCreate(ProductGroupBase):
    product_ids: Optional[List[UUID4]] = Field(default_factory=list, description="لیست محصولات")


class ProductGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    reseller_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    customer_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class ProductGroupResponse(ProductGroupBase):
    id: UUID4
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Service Plan Schemas
class ServicePlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    plan_type: PlanType
    data_limit_gb: Optional[int] = Field(None, ge=0)
    duration_days: int = Field(..., ge=1)
    device_limit: int = Field(default=1, ge=1)
    credit_cost: Decimal = Field(..., ge=0)
    custom_params: Optional[Dict[str, Any]] = None


class ServicePlanCreate(ServicePlanBase):
    product_id: UUID4


class ServicePlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    data_limit_gb: Optional[int] = Field(None, ge=0)
    duration_days: Optional[int] = Field(None, ge=1)
    device_limit: Optional[int] = Field(None, ge=1)
    credit_cost: Optional[Decimal] = Field(None, ge=0)
    custom_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ServicePlanResponse(ServicePlanBase):
    id: UUID4
    product_id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
