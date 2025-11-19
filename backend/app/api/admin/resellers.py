"""
Admin API: Reseller Management
مدیریت نمایندگان و گروه‌ها با پشتیبانی Many-to-Many
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...models import User, Reseller, ResellerGroup, CreditBalance, UserRole
from ...models.user import reseller_group_association
from ...schemas.user import (
    ResellerCreate, ResellerUpdate, ResellerResponse,
    ResellerGroupCreate, ResellerGroupUpdate, ResellerGroupResponse,
    ResellerGroupAssignment
)
from ...api.deps import get_current_admin_user
from ...security import get_password_hash

router = APIRouter()


# ==================== Resellers ====================

@router.get("/resellers", response_model=List[ResellerResponse])
def get_resellers(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
    group_id: Optional[UUID] = Query(None, description="فیلتر بر اساس گروه"),
    search: Optional[str] = Query(None, description="جستجو در نام، username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    لیست نمایندگان با فیلتر و جستجو
    """
    query = db.query(Reseller).options(
        joinedload(Reseller.user),
        joinedload(Reseller.groups)
    )

    # فیلتر بر اساس گروه (Many-to-Many)
    if group_id:
        query = query.join(Reseller.groups).filter(ResellerGroup.id == group_id)

    # جستجو
    if search:
        search_pattern = f"%{search}%"
        query = query.join(Reseller.user).filter(
            (User.username.ilike(search_pattern)) |
            (Reseller.full_name.ilike(search_pattern))
        )

    resellers = query.offset(skip).limit(limit).all()
    return resellers


@router.post("/resellers", response_model=ResellerResponse, status_code=status.HTTP_201_CREATED)
def create_reseller(
    reseller_data: ResellerCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    ایجاد نماینده جدید با پشتیبانی Many-to-Many groups
    """
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

    # بررسی تکراری نبودن referral_code (در صورت وجود)
    if reseller_data.referral_code:
        if db.query(Reseller).filter(Reseller.referral_code == reseller_data.referral_code).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این کد معرف قبلاً استفاده شده است"
            )

    # بررسی وجود گروه‌ها (در صورت ارسال)
    groups = []
    if reseller_data.group_ids:
        groups = db.query(ResellerGroup).filter(ResellerGroup.id.in_(reseller_data.group_ids)).all()
        if len(groups) != len(reseller_data.group_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="یک یا چند گروه یافت نشد"
            )

    # ایجاد User
    user = User(
        username=reseller_data.username,
        email=reseller_data.email,
        hashed_password=get_password_hash(reseller_data.password),
        role=UserRole.RESELLER,
        is_active=True
    )

    db.add(user)
    db.flush()  # برای دریافت user.id

    # ایجاد Reseller
    reseller = Reseller(
        user_id=user.id,
        full_name=reseller_data.full_name,
        phone=reseller_data.phone,
        telegram=reseller_data.telegram,
        referral_code=reseller_data.referral_code
    )

    db.add(reseller)
    db.flush()  # برای دریافت reseller.id

    # افزودن به گروه‌ها (Many-to-Many)
    if groups:
        reseller.groups.extend(groups)

    # ایجاد موجودی کریدیت
    credit_balance = CreditBalance(
        user_id=user.id,
        balance=reseller_data.initial_credit or 0
    )

    db.add(credit_balance)
    db.commit()
    db.refresh(reseller)

    return reseller


@router.get("/resellers/{reseller_id}", response_model=ResellerResponse)
def get_reseller(
    reseller_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    دریافت اطلاعات یک نماینده
    """
    reseller = db.query(Reseller).options(
        joinedload(Reseller.user),
        joinedload(Reseller.groups)
    ).filter(Reseller.id == reseller_id).first()

    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نماینده یافت نشد"
        )

    return reseller


@router.patch("/resellers/{reseller_id}", response_model=ResellerResponse)
def update_reseller(
    reseller_id: UUID,
    reseller_data: ResellerUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    بروزرسانی نماینده
    """
    reseller = db.query(Reseller).filter(Reseller.id == reseller_id).first()

    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نماینده یافت نشد"
        )

    # بررسی تکراری نبودن referral_code (در صورت تغییر)
    if reseller_data.referral_code and reseller_data.referral_code != reseller.referral_code:
        existing = db.query(Reseller).filter(Reseller.referral_code == reseller_data.referral_code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این کد معرف قبلاً استفاده شده است"
            )

    # بروزرسانی فیلدها
    for field, value in reseller_data.model_dump(exclude_unset=True).items():
        setattr(reseller, field, value)

    db.commit()
    db.refresh(reseller)

    return reseller


@router.delete("/resellers/{reseller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reseller(
    reseller_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    حذف نماینده
    """
    reseller = db.query(Reseller).filter(Reseller.id == reseller_id).first()

    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نماینده یافت نشد"
        )

    # حذف User مرتبط (cascade)
    user = db.query(User).filter(User.id == reseller.user_id).first()
    if user:
        db.delete(user)

    db.delete(reseller)
    db.commit()


# ==================== Reseller-Group Management (Many-to-Many) ====================

@router.post("/resellers/{reseller_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_reseller_to_group(
    reseller_id: UUID,
    group_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    افزودن نماینده به گروه
    """
    reseller = db.query(Reseller).filter(Reseller.id == reseller_id).first()
    if not reseller:
        raise HTTPException(status_code=404, detail="نماینده یافت نشد")

    group = db.query(ResellerGroup).filter(ResellerGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="گروه یافت نشد")

    # بررسی عضویت قبلی
    if group in reseller.groups:
        raise HTTPException(status_code=400, detail="نماینده قبلاً عضو این گروه است")

    reseller.groups.append(group)
    db.commit()


@router.delete("/resellers/{reseller_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_reseller_from_group(
    reseller_id: UUID,
    group_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    حذف نماینده از گروه
    """
    reseller = db.query(Reseller).filter(Reseller.id == reseller_id).first()
    if not reseller:
        raise HTTPException(status_code=404, detail="نماینده یافت نشد")

    group = db.query(ResellerGroup).filter(ResellerGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="گروه یافت نشد")

    # بررسی عضویت
    if group not in reseller.groups:
        raise HTTPException(status_code=400, detail="نماینده عضو این گروه نیست")

    reseller.groups.remove(group)
    db.commit()


@router.get("/resellers/{reseller_id}/groups", response_model=List[ResellerGroupResponse])
def get_reseller_groups(
    reseller_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    دریافت لیست گروه‌های یک نماینده
    """
    reseller = db.query(Reseller).options(joinedload(Reseller.groups)).filter(Reseller.id == reseller_id).first()
    if not reseller:
        raise HTTPException(status_code=404, detail="نماینده یافت نشد")

    return reseller.groups


# ==================== Reseller Groups ====================

@router.get("/reseller-groups", response_model=List[ResellerGroupResponse])
def get_reseller_groups_list(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
    is_active: Optional[bool] = Query(None)
):
    """
    لیست گروه‌های نمایندگی
    """
    query = db.query(ResellerGroup)

    if is_active is not None:
        query = query.filter(ResellerGroup.is_active == is_active)

    groups = query.all()
    return groups


@router.post("/reseller-groups", response_model=ResellerGroupResponse, status_code=status.HTTP_201_CREATED)
def create_reseller_group(
    group_data: ResellerGroupCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    ایجاد گروه نمایندگی
    """
    if db.query(ResellerGroup).filter(ResellerGroup.name == group_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="گروهی با این نام قبلاً ایجاد شده است"
        )

    group = ResellerGroup(**group_data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)

    return group


@router.get("/reseller-groups/{group_id}", response_model=ResellerGroupResponse)
def get_reseller_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    دریافت اطلاعات یک گروه
    """
    group = db.query(ResellerGroup).filter(ResellerGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="گروه یافت نشد")

    return group


@router.patch("/reseller-groups/{group_id}", response_model=ResellerGroupResponse)
def update_reseller_group(
    group_id: UUID,
    group_data: ResellerGroupUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    بروزرسانی گروه نمایندگی
    """
    group = db.query(ResellerGroup).filter(ResellerGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="گروه یافت نشد"
        )

    for field, value in group_data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)

    return group


@router.delete("/reseller-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reseller_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    حذف گروه نمایندگی
    """
    group = db.query(ResellerGroup).filter(ResellerGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="گروه یافت نشد"
        )

    db.delete(group)
    db.commit()


@router.get("/reseller-groups/{group_id}/resellers", response_model=List[ResellerResponse])
def get_group_resellers(
    group_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    دریافت لیست نمایندگان یک گروه
    """
    group = db.query(ResellerGroup).options(joinedload(ResellerGroup.resellers)).filter(ResellerGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="گروه یافت نشد")

    return group.resellers
