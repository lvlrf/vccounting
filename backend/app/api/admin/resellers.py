"""
Admin API: Reseller Management
مدیریت نمایندگان و گروه‌ها
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ...database import get_db
from ...models import User, Reseller, ResellerGroup, CreditBalance, UserRole
from ...schemas.user import (
    ResellerCreate, ResellerUpdate, ResellerResponse,
    ResellerGroupCreate, ResellerGroupUpdate, ResellerGroupResponse
)
from ...utils.dependencies import get_current_admin
from ...utils.security import hash_password

router = APIRouter()


# ==================== Resellers ====================

@router.get("/resellers", response_model=List[ResellerResponse])
def get_resellers(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    group_id: UUID = None,
    skip: int = 0,
    limit: int = 100
):
    """لیست نمایندگان"""
    query = db.query(Reseller)

    if group_id:
        query = query.filter(Reseller.group_id == group_id)

    resellers = query.offset(skip).limit(limit).all()
    return resellers


@router.post("/resellers", response_model=ResellerResponse, status_code=status.HTTP_201_CREATED)
def create_reseller(
    reseller_data: ResellerCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """ایجاد نماینده جدید"""
    # بررسی تکراری نبودن username
    if db.query(User).filter(User.username == reseller_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این نام کاربری قبلاً استفاده شده است"
        )

    # بررسی تکراری نبودن email
    if db.query(User).filter(User.email == reseller_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این ایمیل قبلاً استفاده شده است"
        )

    # ایجاد User
    user = User(
        username=reseller_data.username,
        email=reseller_data.email,
        hashed_password=hash_password(reseller_data.password),
        role=UserRole.RESELLER,
        is_active=True
    )

    db.add(user)
    db.flush()  # برای دریافت user.id

    # ایجاد Reseller
    reseller = Reseller(
        user_id=user.id,
        group_id=reseller_data.group_id,
        full_name=reseller_data.full_name,
        phone=reseller_data.phone,
        telegram=reseller_data.telegram
    )

    db.add(reseller)

    # ایجاد موجودی کریدیت
    # اگر گروه دارد، از default_credit گروه استفاده کن
    initial_credit = 0
    if reseller_data.group_id:
        group = db.query(ResellerGroup).get(reseller_data.group_id)
        if group:
            initial_credit = group.default_credit

    credit_balance = CreditBalance(
        user_id=user.id,
        balance=initial_credit
    )

    db.add(credit_balance)
    db.commit()
    db.refresh(reseller)

    return reseller


@router.get("/resellers/{reseller_id}", response_model=ResellerResponse)
def get_reseller(
    reseller_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """دریافت اطلاعات یک نماینده"""
    reseller = db.query(Reseller).get(reseller_id)

    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نماینده یافت نشد"
        )

    return reseller


@router.put("/resellers/{reseller_id}", response_model=ResellerResponse)
def update_reseller(
    reseller_id: UUID,
    reseller_data: ResellerUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """بروزرسانی نماینده"""
    reseller = db.query(Reseller).get(reseller_id)

    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نماینده یافت نشد"
        )

    # بروزرسانی فیلدها
    for field, value in reseller_data.dict(exclude_unset=True).items():
        setattr(reseller, field, value)

    db.commit()
    db.refresh(reseller)

    return reseller


@router.delete("/resellers/{reseller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reseller(
    reseller_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """حذف نماینده"""
    reseller = db.query(Reseller).get(reseller_id)

    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نماینده یافت نشد"
        )

    # حذف User مرتبط
    user = db.query(User).get(reseller.user_id)
    if user:
        db.delete(user)

    db.delete(reseller)
    db.commit()


# ==================== Reseller Groups ====================

@router.get("/reseller-groups", response_model=List[ResellerGroupResponse])
def get_reseller_groups(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """لیست گروه‌های نمایندگی"""
    groups = db.query(ResellerGroup).all()
    return groups


@router.post("/reseller-groups", response_model=ResellerGroupResponse, status_code=status.HTTP_201_CREATED)
def create_reseller_group(
    group_data: ResellerGroupCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """ایجاد گروه نمایندگی"""
    if db.query(ResellerGroup).filter(ResellerGroup.name == group_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="گروهی با این نام قبلاً ایجاد شده است"
        )

    group = ResellerGroup(**group_data.dict())
    db.add(group)
    db.commit()
    db.refresh(group)

    return group


@router.put("/reseller-groups/{group_id}", response_model=ResellerGroupResponse)
def update_reseller_group(
    group_id: UUID,
    group_data: ResellerGroupUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """بروزرسانی گروه نمایندگی"""
    group = db.query(ResellerGroup).get(group_id)

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


@router.delete("/reseller-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reseller_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """حذف گروه نمایندگی"""
    group = db.query(ResellerGroup).get(group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="گروه یافت نشد"
        )

    db.delete(group)
    db.commit()
