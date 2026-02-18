"""API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import require_roles
from app.models.user import User
from app.models.user import UserRole

router = APIRouter()


@router.get("/")
async def api_root():
    """API root - returns service info."""
    return {"service": "qao-inmate-api", "version": "0.1.0"}


@router.get("/staff-only")
async def staff_only(
    current_user: Annotated[User, Depends(require_roles(UserRole.ATTORNEY, UserRole.PARALEGAL))],
):
    """Example: requires attorney or paralegal role."""
    return {"message": f"Hello, {current_user.full_name}. Staff access granted."}
