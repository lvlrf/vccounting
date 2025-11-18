"""
Admin API: Product Management
مدیریت محصولات، گروه‌ها و پلن‌ها
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ...database import get_db
from ...models import User, Product, ProductGroup, ProductGroupItem, ServicePlan
from ...schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductGroupCreate, ProductGroupUpdate, ProductGroupResponse,
    ServicePlanCreate, ServicePlanUpdate, ServicePlanResponse
)
from ...utils.dependencies import get_current_admin

router = APIRouter()


# ==================== Products ====================

@router.get("/products", response_model=List[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100
):
    """لیست تمام محصولات"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """ایجاد محصول جدید"""
    # بررسی تکراری نبودن نام
    if db.query(Product).filter(Product.name == product_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="محصولی با این نام قبلاً ایجاد شده است"
        )

    product = Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """دریافت اطلاعات یک محصول"""
    product = db.query(Product).get(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="محصول یافت نشد"
        )

    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """بروزرسانی محصول"""
    product = db.query(Product).get(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="محصول یافت نشد"
        )

    # بروزرسانی فیلدها
    for field, value in product_data.dict(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """حذف محصول"""
    product = db.query(Product).get(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="محصول یافت نشد"
        )

    db.delete(product)
    db.commit()


# ==================== Product Groups ====================

@router.get("/product-groups", response_model=List[ProductGroupResponse])
def get_product_groups(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """لیست گروه‌های محصول"""
    groups = db.query(ProductGroup).all()
    return groups


@router.post("/product-groups", response_model=ProductGroupResponse, status_code=status.HTTP_201_CREATED)
def create_product_group(
    group_data: ProductGroupCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """ایجاد گروه محصول"""
    if db.query(ProductGroup).filter(ProductGroup.name == group_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="گروهی با این نام قبلاً ایجاد شده است"
        )

    group = ProductGroup(
        name=group_data.name,
        description=group_data.description
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    # افزودن محصولات به گروه
    if group_data.product_ids:
        for product_id in group_data.product_ids:
            item = ProductGroupItem(
                product_id=product_id,
                group_id=group.id
            )
            db.add(item)

        db.commit()

    return group


@router.put("/product-groups/{group_id}", response_model=ProductGroupResponse)
def update_product_group(
    group_id: UUID,
    group_data: ProductGroupUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """بروزرسانی گروه محصول"""
    group = db.query(ProductGroup).get(group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="گروه یافت نشد"
        )

    for field, value in group_data.dict(exclude_unset=True).items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)

    return group


# ==================== Service Plans ====================

@router.get("/service-plans", response_model=List[ServicePlanResponse])
def get_service_plans(
    product_id: UUID = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """لیست پلن‌های سرویس"""
    query = db.query(ServicePlan)

    if product_id:
        query = query.filter(ServicePlan.product_id == product_id)

    plans = query.all()
    return plans


@router.post("/service-plans", response_model=ServicePlanResponse, status_code=status.HTTP_201_CREATED)
def create_service_plan(
    plan_data: ServicePlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """ایجاد پلن سرویس"""
    # بررسی وجود محصول
    product = db.query(Product).get(plan_data.product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="محصول یافت نشد"
        )

    plan = ServicePlan(**plan_data.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


@router.put("/service-plans/{plan_id}", response_model=ServicePlanResponse)
def update_service_plan(
    plan_id: UUID,
    plan_data: ServicePlanUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """بروزرسانی پلن سرویس"""
    plan = db.query(ServicePlan).get(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پلن یافت نشد"
        )

    for field, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)

    return plan


@router.delete("/service-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """حذف پلن سرویس"""
    plan = db.query(ServicePlan).get(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پلن یافت نشد"
        )

    db.delete(plan)
    db.commit()
