"""
Reseller API Endpoints
API نمایندگان: مدیریت اکانت‌ها و کریدیت
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..models import Reseller, AccountStatus
from ..schemas.account import (
    CustomerAccountCreate, CustomerAccountUpdate, CustomerAccountResponse,
    RenewAccountRequest, AddTrafficRequest, ToggleStatusRequest
)
from ..schemas.credit import CreditBalanceResponse, CreditTransactionResponse
from ..services.account_service import AccountService
from ..services.credit_service import CreditService
from ..utils.dependencies import get_current_reseller
from ..services.panel_integrations import PanelOperationError

router = APIRouter()


# ==================== Credit ====================

@router.get("/credit/balance", response_model=CreditBalanceResponse)
def get_credit_balance(
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """دریافت موجودی کریدیت"""
    balance = CreditService.get_or_create_balance(db, str(reseller.user_id))
    return balance


@router.get("/credit/transactions", response_model=List[CreditTransactionResponse])
def get_credit_transactions(
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """تاریخچه تراکنش‌های کریدیت"""
    transactions = CreditService.get_transactions(
        db=db,
        reseller_id=str(reseller.user_id),
        limit=limit,
        offset=skip
    )

    return transactions


# ==================== Accounts ====================

@router.get("/accounts", response_model=List[CustomerAccountResponse])
def get_accounts(
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db),
    status: Optional[AccountStatus] = None,
    product_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    لیست اکانت‌های مشتری

    - status: فیلتر بر اساس وضعیت (active, inactive, expired, deleted)
    - product_id: فیلتر بر اساس محصول
    """
    accounts = AccountService.get_accounts(
        db=db,
        reseller_id=str(reseller.id),
        status=status,
        product_id=str(product_id) if product_id else None,
        limit=limit,
        offset=skip
    )

    return accounts


@router.post("/accounts", response_model=CustomerAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: CustomerAccountCreate,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    ایجاد اکانت جدید

    **مراحل**:
    1. بررسی دسترسی به محصول
    2. کسر کریدیت
    3. ایجاد در پنل
    4. ذخیره در دیتابیس
    """
    try:
        account, subscription_url = await AccountService.create_account(
            db=db,
            reseller_id=str(reseller.id),
            product_id=str(account_data.product_id),
            service_plan_id=str(account_data.service_plan_id),
            username=account_data.username,
            customer_name=account_data.customer_name,
            customer_note=account_data.customer_note
        )

        return account

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PanelOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/accounts/{account_id}", response_model=CustomerAccountResponse)
def get_account(
    account_id: UUID,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """دریافت جزئیات یک اکانت"""
    from ..models import CustomerAccount

    account = db.query(CustomerAccount).get(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="اکانت یافت نشد"
        )

    if str(account.reseller_id) != str(reseller.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="این اکانت متعلق به شما نیست"
        )

    return account


@router.put("/accounts/{account_id}", response_model=CustomerAccountResponse)
def update_account(
    account_id: UUID,
    account_data: CustomerAccountUpdate,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """بروزرسانی اطلاعات اکانت (نام مشتری، یادداشت)"""
    from ..models import CustomerAccount

    account = db.query(CustomerAccount).get(account_id)

    if not account or str(account.reseller_id) != str(reseller.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="اکانت یافت نشد"
        )

    # بروزرسانی فیلدهای مجاز
    for field, value in account_data.dict(exclude_unset=True).items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)

    return account


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: UUID,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    حذف اکانت با برگشت کریدیت

    کریدیت بر اساس زمان و حجم باقیمانده محاسبه و برگردانده می‌شود
    """
    try:
        refund_amount = await AccountService.delete_account(
            db=db,
            account_id=str(account_id),
            reseller_id=str(reseller.id)
        )

        return {
            "message": "اکانت با موفقیت حذف شد",
            "refund_amount": float(refund_amount)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/accounts/{account_id}/renew", response_model=CustomerAccountResponse)
async def renew_account(
    account_id: UUID,
    data: RenewAccountRequest,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    تمدید اکانت (افزودن زمان)

    کریدیت متناسب با تعداد روز کسر می‌شود
    """
    try:
        account = await AccountService.renew_account(
            db=db,
            account_id=str(account_id),
            reseller_id=str(reseller.id),
            days=data.days
        )

        return account

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PanelOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/accounts/{account_id}/add-traffic", response_model=CustomerAccountResponse)
async def add_traffic(
    account_id: UUID,
    data: AddTrafficRequest,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    افزودن حجم به اکانت

    فقط برای اکانت‌هایی که حجم محدود دارند
    """
    try:
        account = await AccountService.add_traffic(
            db=db,
            account_id=str(account_id),
            reseller_id=str(reseller.id),
            gb=data.gb
        )

        return account

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PanelOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/accounts/{account_id}/toggle-status", response_model=CustomerAccountResponse)
async def toggle_account_status(
    account_id: UUID,
    data: ToggleStatusRequest,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    فعال/غیرفعال کردن اکانت

    برای توقف موقت سرویس بدون حذف اکانت
    """
    try:
        account = await AccountService.toggle_status(
            db=db,
            account_id=str(account_id),
            reseller_id=str(reseller.id),
            enabled=data.enabled
        )

        return account

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PanelOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/accounts/{account_id}/sync", response_model=CustomerAccountResponse)
async def sync_account(
    account_id: UUID,
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    همگام‌سازی اطلاعات اکانت از پنل

    دریافت آخرین وضعیت میزان استفاده و تاریخ انقضا
    """
    account = await AccountService.sync_from_panel(
        db=db,
        account_id=str(account_id)
    )

    if str(account.reseller_id) != str(reseller.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="این اکانت متعلق به شما نیست"
        )

    return account


# ==================== Stats ====================

@router.get("/stats/overview")
def get_overview_stats(
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db)
):
    """
    آمار کلی نماینده
    """
    from ..models import CustomerAccount
    from sqlalchemy import func

    # تعداد اکانت‌های فعال
    active_accounts = db.query(func.count(CustomerAccount.id)).filter(
        CustomerAccount.reseller_id == reseller.id,
        CustomerAccount.status == AccountStatus.ACTIVE
    ).scalar()

    # تعداد اکانت‌های منقضی شده
    expired_accounts = db.query(func.count(CustomerAccount.id)).filter(
        CustomerAccount.reseller_id == reseller.id,
        CustomerAccount.status == AccountStatus.EXPIRED
    ).scalar()

    # موجودی کریدیت
    balance = CreditService.get_or_create_balance(db, str(reseller.user_id))

    return {
        "total_accounts_created": int(reseller.total_accounts_created),
        "active_accounts": active_accounts,
        "expired_accounts": expired_accounts,
        "credit_balance": float(balance.balance),
        "total_credit_spent": float(reseller.total_credit_spent),
        "total_credit_purchased": float(reseller.total_credit_purchased)
    }
