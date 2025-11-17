"""
FastAPI Dependencies
Dependency های مورد استفاده در endpoints
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import User, UserRole, Reseller
from .security import decode_access_token

# HTTP Bearer برای دریافت token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    دریافت کاربر فعلی از JWT token

    Raises:
        HTTPException: اگر token نامعتبر باشد یا کاربر پیدا نشود
    """
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # دریافت کاربر از دیتابیس
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="کاربر یافت نشد",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است"
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    اطمینان از اینکه کاربر فعلی Admin است

    Raises:
        HTTPException: اگر کاربر Admin نباشد
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="دسترسی محدود به ادمین"
        )
    return current_user


async def get_current_reseller(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Reseller:
    """
    اطمینان از اینکه کاربر فعلی Reseller است و دریافت پروفایل نماینده

    Raises:
        HTTPException: اگر کاربر Reseller نباشد
    """
    if current_user.role != UserRole.RESELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="دسترسی محدود به نمایندگان"
        )

    reseller = db.query(Reseller).filter(Reseller.user_id == current_user.id).first()
    if not reseller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پروفایل نماینده یافت نشد"
        )

    return reseller


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    دریافت کاربر فعلی (اختیاری)
    برای endpoints که هم برای کاربران لاگین و هم غیرلاگین قابل دسترس هستند

    Returns:
        User object یا None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
