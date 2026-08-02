"""Password hashing and JWT utilities."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return pwd_context.hash(password)


def _create_token(subject: Union[str, Any], token_version: int, token_type: str, expire_minutes: int) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {"exp": expire, "sub": str(subject), "ver": token_version, "type": token_type}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: Union[str, Any], token_version: int) -> str:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    return _create_token(subject, token_version, "access", settings.JWT_EXPIRE_MINUTES)


def create_refresh_token(subject: Union[str, Any], token_version: int) -> str:
    """Create a longer-lived JWT refresh token, used only to mint new access tokens."""
    settings = get_settings()
    return _create_token(subject, token_version, "refresh", settings.JWT_REFRESH_EXPIRE_MINUTES)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT, returning its full payload, or None if invalid/expired."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
