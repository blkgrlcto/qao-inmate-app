"""FastAPI dependencies for auth and role-based access."""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.models.user import UserRole

security = HTTPBearer()

_INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current user from a JWT access token (rejects refresh tokens and
    tokens issued before the user's most recent revocation)."""
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise _INVALID_TOKEN
    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError:
        raise _INVALID_TOKEN
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise _INVALID_TOKEN
    if payload.get("ver") != user.token_version:
        raise _INVALID_TOKEN
    return user


def require_roles(*allowed_roles: UserRole):
    """Dependency factory: require user to have one of the given roles."""

    async def role_guard(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        role_value = current_user.role if isinstance(current_user.role, str) else current_user.role.value
        allowed_values = {r.value for r in allowed_roles}
        if role_value not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {', '.join(allowed_values)}",
            )
        return current_user

    return role_guard
