"""
Admin API: Credit Management
مدیریت کریدیت نمایندگان
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from decimal import Decimal

from ...database import get_db
from ...models import User
from ...schemas.credit import (
    ManualCreditAdd, ManualCreditDeduct,
    CreditTransactionResponse, CreditBalanceResponse
)
from ...services.credit_service import CreditService
from ...utils.dependencies import get_current_admin

router = APIRouter()


@router.post("/credit/add", response_model=CreditTransactionResponse)
def add_credit(
    data: ManualCreditAdd,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    شارژ کریدیت نماینده (توسط ادمین)
    """
    try:
        transaction = CreditService.add_credit(
            db=db,
            reseller_id=str(data.reseller_id),
            amount=data.amount,
            admin_id=str(admin.id),
            note=data.admin_note
        )

        return transaction

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/credit/deduct", response_model=CreditTransactionResponse)
def deduct_credit(
    data: ManualCreditDeduct,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    کسر کریدیت نماینده (توسط ادمین)
    """
    try:
        transaction = CreditService.deduct_credit(
            db=db,
            reseller_id=str(data.reseller_id),
            amount=data.amount,
            admin_id=str(admin.id),
            note=data.admin_note
        )

        return transaction

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/credit/balance/{reseller_id}", response_model=CreditBalanceResponse)
def get_reseller_balance(
    reseller_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    دریافت موجودی کریدیت یک نماینده
    """
    balance = CreditService.get_or_create_balance(db, str(reseller_id))
    return balance


@router.get("/credit/transactions", response_model=List[CreditTransactionResponse])
def get_all_transactions(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    reseller_id: UUID = None,
    skip: int = 0,
    limit: int = 100
):
    """
    دریافت تاریخچه تراکنش‌ها

    - reseller_id: فیلتر بر اساس نماینده (اختیاری)
    """
    transactions = CreditService.get_transactions(
        db=db,
        reseller_id=str(reseller_id) if reseller_id else None,
        limit=limit,
        offset=skip
    )

    return transactions
