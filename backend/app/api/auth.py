"""
Authentication API Endpoints
احراز هویت: ثبت‌نام، ورود، تمدید token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, UserRole, Reseller, CreditBalance
from ..schemas.user import (
    LoginRequest, LoginResponse, UserResponse,
    UserCreate, ChangePasswordRequest
)
from ..utils.security import (
    verify_password, hash_password, create_access_token
)
from ..utils.dependencies import get_current_user
from ..config import settings

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    ورود به سیستم

    - دریافت username و password
    - بررسی اعتبار
    - ایجاد JWT token
    """
    # جستجوی کاربر
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است"
        )

    # بررسی رمز عبور
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است"
        )

    # بررسی فعال بودن کاربر
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری شما غیرفعال است"
        )

    # بروزرسانی آخرین ورود
    user.last_login = datetime.utcnow()
    db.commit()

    # ایجاد token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value
        },
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    ثبت‌نام کاربر جدید

    **نکته**: در production این endpoint باید محدود شود
    یا فقط برای Admin در دسترس باشد
    """
    # بررسی تکراری نبودن username
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این نام کاربری قبلاً استفاده شده است"
        )

    # بررسی تکراری نبودن email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این ایمیل قبلاً استفاده شده است"
        )

    # ایجاد کاربر
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # اگر Reseller است، ایجاد پروفایل و موجودی کریدیت
    if user.role == UserRole.RESELLER:
        reseller = Reseller(user_id=user.id)
        db.add(reseller)

        credit_balance = CreditBalance(user_id=user.id, balance=0)
        db.add(credit_balance)

        db.commit()

    return UserResponse.from_orm(user)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    دریافت اطلاعات کاربر فعلی
    """
    return UserResponse.from_orm(current_user)


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تغییر رمز عبور
    """
    # بررسی رمز عبور فعلی
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز عبور فعلی اشتباه است"
        )

    # تغییر رمز عبور
    current_user.hashed_password = hash_password(data.new_password)
    current_user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "رمز عبور با موفقیت تغییر یافت"}


@router.post("/refresh")
def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    تمدید token
    """
    access_token = create_access_token(
        data={
            "sub": str(current_user.id),
            "username": current_user.username,
            "role": current_user.role.value
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout():
    """
    خروج از سیستم

    در client-side token را حذف کنید
    در سمت سرور نیازی به invalidate کردن نیست
    (در صورت نیاز می‌توان blacklist پیاده‌سازی کرد)
    """
    return {"message": "با موفقیت خارج شدید"}
