"""Authentication routes."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Login with email and password. Returns a short-lived access token and a
    longer-lived refresh token."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(subject=str(user.id), token_version=user.token_version),
        "refresh_token": create_refresh_token(subject=str(user.id), token_version=user.token_version),
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: str = Body(..., embed=True),
) -> dict:
    """Exchange a valid refresh token for a new access token."""
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise invalid
    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError:
        raise invalid

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or payload.get("ver") != user.token_version:
        raise invalid

    return {
        "access_token": create_access_token(subject=str(user.id), token_version=user.token_version),
        "token_type": "bearer",
    }


@router.get("/me")
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Return current authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }
