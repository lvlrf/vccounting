"""
Admin Customer Management API
مدیریت مشتریان توسط ادمین
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ...database import get_db
from ...models import Customer, Subscription, User, Reseller
from ...schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerWithStats,
    CustomerListResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse,
)
from ...api.deps import get_current_admin_user
from ...security import get_password_hash

router = APIRouter()


# ==================== Customer Endpoints ====================

@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    ایجاد مشتری جدید
    فقط ادمین می‌تواند مشتری ایجاد کند
    """
    # بررسی تکراری نبودن ایمیل
    if customer_data.email:
        existing = db.query(Customer).filter(Customer.email == customer_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    # بررسی وجود نماینده (در صورت ارجاع)
    if customer_data.representative_id:
        reseller = db.query(Reseller).filter(Reseller.id == customer_data.representative_id).first()
        if not reseller:
            raise HTTPException(status_code=404, detail="Representative not found")

    # ایجاد مشتری
    customer = Customer(
        full_name=customer_data.full_name,
        email=customer_data.email,
        phone=customer_data.phone,
        telegram_chat_id=customer_data.telegram_chat_id,
        telegram_username=customer_data.telegram_username,
        representative_id=customer_data.representative_id,
        notes=customer_data.notes,
        password_hash=get_password_hash(customer_data.password) if customer_data.password else None,
        is_active=True
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="جستجو در نام، ایمیل، شماره"),
    representative_id: Optional[UUID] = Query(None, description="فیلتر بر اساس نماینده"),
    is_active: Optional[bool] = Query(None, description="فیلتر بر اساس وضعیت"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    دریافت لیست مشتریان با فیلتر و جستجو
    """
    query = db.query(Customer)

    # اعمال فیلترها
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.full_name.ilike(search_pattern)) |
            (Customer.email.ilike(search_pattern)) |
            (Customer.phone.ilike(search_pattern))
        )

    if representative_id:
        query = query.filter(Customer.representative_id == representative_id)

    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)

    # محاسبه تعداد کل
    total = query.count()

    # دریافت با pagination
    customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()

    return CustomerListResponse(
        customers=customers,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/{customer_id}", response_model=CustomerWithStats)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    دریافت اطلاعات یک مشتری با آمار
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # محاسبه آمار
    total_subscriptions = db.query(Subscription).filter(
        Subscription.customer_id == customer_id
    ).count()

    active_subscriptions = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.is_active == True,
        Subscription.expires_at > datetime.utcnow()
    ).count()

    total_accounts = len(customer.accounts) if customer.accounts else 0

    # ساخت response
    customer_dict = {
        "id": customer.id,
        "full_name": customer.full_name,
        "email": customer.email,
        "phone": customer.phone,
        "telegram_chat_id": customer.telegram_chat_id,
        "telegram_username": customer.telegram_username,
        "representative_id": customer.representative_id,
        "notes": customer.notes,
        "is_active": customer.is_active,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "total_accounts": total_accounts
    }

    return CustomerWithStats(**customer_dict)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    بروزرسانی اطلاعات مشتری
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # بررسی تکراری نبودن ایمیل (در صورت تغییر)
    if customer_data.email and customer_data.email != customer.email:
        existing = db.query(Customer).filter(Customer.email == customer_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    # بروزرسانی فیلدها
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return customer


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    حذف مشتری
    توجه: اشتراک‌ها و اکانت‌های مرتبط نیز حذف می‌شوند
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    db.delete(customer)
    db.commit()

    return None


# ==================== Subscription Endpoints ====================

@router.post("/{customer_id}/subscriptions", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    customer_id: UUID,
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    ایجاد اشتراک جدید برای مشتری
    """
    # بررسی وجود مشتری
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # ایجاد اشتراک
    subscription = Subscription(
        customer_id=customer_id,
        plan=subscription_data.plan,
        starts_at=subscription_data.starts_at or datetime.utcnow(),
        expires_at=subscription_data.expires_at,
        auto_renew=subscription_data.auto_renew,
        is_active=True
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # محاسبه فیلدهای مشتق شده
    subscription.is_expired = subscription.expires_at < datetime.utcnow()
    subscription.days_remaining = max(0, (subscription.expires_at - datetime.utcnow()).days)

    return subscription


@router.get("/{customer_id}/subscriptions", response_model=SubscriptionListResponse)
async def list_customer_subscriptions(
    customer_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    دریافت لیست اشتراک‌های یک مشتری
    """
    # بررسی وجود مشتری
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # دریافت اشتراک‌ها
    query = db.query(Subscription).filter(Subscription.customer_id == customer_id)
    total = query.count()

    subscriptions = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()

    # محاسبه فیلدهای مشتق شده
    for sub in subscriptions:
        sub.is_expired = sub.expires_at < datetime.utcnow()
        sub.days_remaining = max(0, (sub.expires_at - datetime.utcnow()).days)

    return SubscriptionListResponse(
        subscriptions=subscriptions,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.patch("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    subscription_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    بروزرسانی اشتراک
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # بروزرسانی فیلدها
    update_data = subscription_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)

    db.commit()
    db.refresh(subscription)

    # محاسبه فیلدهای مشتق شده
    subscription.is_expired = subscription.expires_at < datetime.utcnow()
    subscription.days_remaining = max(0, (subscription.expires_at - datetime.utcnow()).days)

    return subscription


@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    حذف اشتراک
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()

    return None
