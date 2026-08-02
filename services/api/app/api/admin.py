"""Admin-only endpoints."""
import uuid
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.config import get_settings
from app.core.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.integrations.courtlistener.client import search_pacer_dockets
from app.integrations.courtlistener.query_builder import build_search_query
from app.models.federal_case_cache import FederalCaseCache
from app.models.share import Share
from app.models.user import User
from app.models.user import UserRole

from app.api.federal_cases import _parse_result

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/users")
async def list_users(
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List all users. Admin only."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role if isinstance(u.role, str) else u.role.value,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@admin_router.post("/users")
async def create_user(
    email: str = Body(...),
    password: str = Body(...),
    full_name: str = Body(...),
    role: str = Body(...),
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Create a user. Admin only."""
    if role not in {r.value for r in UserRole}:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A user with that email already exists")

    await log_audit(db, current_user.id, "user_create", "user", str(user.id))

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role if isinstance(user.role, str) else user.role.value,
        "created_at": user.created_at.isoformat(),
    }


@admin_router.get("/shares")
async def list_shares(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List who has access to a case. Admin only."""
    result = await db.execute(
        select(Share, User.email, User.full_name)
        .join(User, User.id == Share.user_id)
        .where(Share.case_id == case_id)
        .order_by(Share.created_at)
    )
    rows = result.all()
    return [
        {
            "id": str(share.id),
            "case_id": str(share.case_id),
            "user_id": str(share.user_id),
            "role": share.role,
            "user_email": email,
            "user_full_name": full_name,
        }
        for share, email, full_name in rows
    ]


@admin_router.post("/shares")
async def create_share(
    case_id: uuid.UUID = Body(...),
    user_id: uuid.UUID = Body(...),
    role: str = Body("viewer"),
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Grant a user access to a case. Admin only."""
    share = Share(case_id=case_id, user_id=user_id, role=role)
    db.add(share)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="This user already has access to this case")

    await log_audit(db, current_user.id, "share_create", "share", str(share.id))

    return {
        "id": str(share.id),
        "case_id": str(share.case_id),
        "user_id": str(share.user_id),
        "role": share.role,
    }


@admin_router.post("/federal-cases/sync")
async def sync_federal_case_cache(
    current_user: Annotated[User, Depends(require_roles(UserRole.ATTORNEY, UserRole.PARALEGAL))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Refresh stale cache entries. Attorney/paralegal only."""
    settings = get_settings()
    stale_threshold = datetime.utcnow() - timedelta(days=settings.FED_CASE_SYNC_STALE_DAYS)

    result = await db.execute(
        select(FederalCaseCache).where(
            FederalCaseCache.last_synced_at < stale_threshold,
            FederalCaseCache.docket_number.isnot(None),
            FederalCaseCache.docket_number != "",
        ).limit(50)
    )
    rows = result.scalars().all()
    if not rows:
        return {"synced": 0, "message": "No stale entries to sync"}

    refreshed = 0
    for row in rows:
        if not row.docket_number:
            continue
        qstring = build_search_query(row.docket_number, "docket", row.court_id)
        if not qstring:
            continue
        try:
            data = await search_pacer_dockets(qstring, page_size=1)
            results_list = data.get("results") or data.get("hits") or []
            if results_list:
                parsed = _parse_result(results_list[0])
                if parsed:
                    row.case_name = parsed.get("case_name")
                    row.court_id = parsed.get("court_id")
                    row.docket_number = parsed.get("docket_number")
                    row.date_filed = parsed.get("date_filed")
                    row.date_terminated = parsed.get("date_terminated")
                    row.parties = parsed.get("parties", [])
                    row.recap_available = parsed.get("recap_available", False)
                    row.absolute_url = parsed.get("absolute_url")
                    row.raw = parsed.get("raw", {})
                    row.last_synced_at = datetime.utcnow()
                    refreshed += 1
        except Exception:
            pass

    return {"synced": refreshed, "message": f"Refreshed {refreshed} of {len(rows)} stale entries"}
