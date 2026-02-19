"""Admin-only endpoints."""
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.integrations.courtlistener.client import search_pacer_dockets
from app.integrations.courtlistener.query_builder import build_search_query
from app.models.federal_case_cache import FederalCaseCache
from app.models.user import User
from app.models.user import UserRole

from app.api.federal_cases import _parse_result

admin_router = APIRouter(prefix="/admin", tags=["admin"])


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
