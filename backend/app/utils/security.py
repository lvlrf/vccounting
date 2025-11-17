"""
Security Utilities
توابع امنیتی: Password Hashing, Encryption, JWT
"""
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets
import json
import base64

from ..config import settings

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    رمزگذاری password با bcrypt
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    بررسی صحت password
    """
    return pwd_context.verify(plain_password, hashed_password)


# Encryption/Decryption (برای ذخیره credentials)
def get_cipher():
    """
    دریافت cipher برای رمزگذاری
    از ENCRYPTION_KEY در تنظیمات استفاده می‌کند
    """
    # اطمینان از اینکه key به اندازه صحیح است (32 bytes for Fernet)
    key = settings.ENCRYPTION_KEY.encode()
    # اگر کوتاه‌تر از 32 بایت است، pad کن
    key = base64.urlsafe_b64encode(key.ljust(32)[:32])
    return Fernet(key)


def encrypt_data(data: Dict) -> str:
    """
    رمزگذاری داده (معمولاً credentials پنل‌ها)

    Args:
        data: دیکشنری برای رمزگذاری

    Returns:
        رشته رمزگذاری شده
    """
    cipher = get_cipher()
    json_data = json.dumps(data)
    encrypted = cipher.encrypt(json_data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> Dict:
    """
    رمزگشایی داده

    Args:
        encrypted_data: رشته رمزگذاری شده

    Returns:
        دیکشنری اصلی
    """
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_data.encode())
    return json.loads(decrypted.decode())


# JWT Tokens
def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    ایجاد JWT token

    Args:
        data: داده‌های داخل token (معمولاً user_id و role)
        expires_delta: مدت اعتبار token

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    رمزگشایی JWT token

    Args:
        token: JWT token string

    Returns:
        داده‌های داخل token یا None در صورت خطا
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_random_password(length: int = 16) -> str:
    """
    تولید password تصادفی

    Args:
        length: طول password

    Returns:
        Password تصادفی
    """
    return secrets.token_urlsafe(length)


def generate_username() -> str:
    """
    تولید username تصادفی برای اکانت‌ها
    فرمت: user_<8 رقم تصادفی>

    Returns:
        Username تصادفی
    """
    return f"user_{secrets.token_hex(4)}"


def generate_api_key() -> str:
    """
    تولید API key تصادفی

    Returns:
        API key
    """
    return secrets.token_urlsafe(32)
