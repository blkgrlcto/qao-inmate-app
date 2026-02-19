"""Federal case search via CourtListener (PACER/RECAP)."""
import re
import uuid
from datetime import date, datetime
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.integrations.courtlistener.client import search_pacer_dockets
from app.integrations.courtlistener.query_builder import build_search_query
from app.models.federal_case_cache import FederalCaseCache
from app.models.federal_case_search_log import FederalCaseSearchLog
from app.models.user import User
from app.models.user import UserRole
from app.utils.federal_case_detect import detect_mode

router = APIRouter(prefix="/federal-cases", tags=["federal-cases"])


def _parse_date(v: Any) -> Optional[date]:
    """Parse ISO date string or None."""
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            pass
    return None


def _extract_cursor(next_url: Optional[str]) -> Optional[str]:
    """Extract cursor from next page URL."""
    if not next_url:
        return None
    match = re.search(r"[?&]cursor=([^&]+)", next_url)
    return match.group(1) if match else None


def _parse_result(hit: dict[str, Any]) -> dict[str, Any]:
    """Map CourtListener hit to cache row fields."""
    raw = hit
    ext_id = hit.get("id") or hit.get("docket_id")
    if ext_id is None:
        return {}

    case_name = hit.get("case_name") or hit.get("caseName") or hit.get("title")
    docket_number = hit.get("docket_number") or hit.get("docketNumber")
    court = hit.get("court") or hit.get("court_id")
    court_id = court.get("id") if isinstance(court, dict) else (court if isinstance(court, str) else None)
    date_filed = _parse_date(hit.get("date_filed") or hit.get("dateFiled"))
    date_terminated = _parse_date(hit.get("date_terminated") or hit.get("dateTerminated"))
    absolute_url = hit.get("absolute_url") or hit.get("absoluteUrl") or hit.get("recap_url") or hit.get("recapUrl")

    parties: list[str] = []
    if "parties" in hit and isinstance(hit["parties"], list):
        for p in hit["parties"]:
            if isinstance(p, dict) and "name" in p:
                parties.append(str(p["name"]))
            elif isinstance(p, str):
                parties.append(p)
    elif "party" in hit and isinstance(hit["party"], str):
        parties = [hit["party"]]

    recap_docs = hit.get("recap_documents") or hit.get("recapDocuments") or []
    recap_available = any(
        (d.get("is_available") or d.get("isAvailable") or False)
        for d in recap_docs
        if isinstance(d, dict)
    )

    return {
        "source": "courtlistener",
        "external_docket_id": int(ext_id),
        "court_id": str(court_id) if court_id else None,
        "case_name": str(case_name)[:1024] if case_name else None,
        "docket_number": str(docket_number)[:128] if docket_number else None,
        "date_filed": date_filed,
        "date_terminated": date_terminated,
        "parties": parties,
        "recap_available": recap_available,
        "absolute_url": str(absolute_url)[:2048] if absolute_url else None,
        "raw": raw,
    }


@router.get("/search")
async def search_federal_cases(
    q: str = Query(..., min_length=1),
    court_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Search federal PACER/RECAP dockets.
    Auto-detects docket number vs party name. Any logged-in role allowed.
    """
    mode, normalized = detect_mode(q)
    if not normalized:
        return {"query": q, "detected_mode": mode, "next_cursor": None, "results": []}

    qstring = build_search_query(normalized, mode, court_id)
    if not qstring:
        return {"query": q, "detected_mode": mode, "next_cursor": None, "results": []}

    try:
        data = await search_pacer_dockets(qstring, cursor=cursor, page_size=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CourtListener error: {str(e)}")

    results_list = data.get("results") or data.get("hits") or []
    next_url = data.get("next")
    next_cursor = _extract_cursor(next_url) if isinstance(next_url, str) else data.get("cursor")

    # Upsert each result into cache
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    now = datetime.utcnow()
    ext_ids: list[int] = []

    for hit in results_list:
        parsed = _parse_result(hit)
        if not parsed:
            continue

        ext_id = parsed["external_docket_id"]
        ext_ids.append(ext_id)

        stmt = pg_insert(FederalCaseCache).values(
            id=uuid.uuid4(),
            **parsed,
            last_seen_at=now,
            last_synced_at=now,
        ).on_conflict_do_update(
            constraint="uq_federal_case_cache_source_ext",
            set_={
                "case_name": parsed.get("case_name"),
                "court_id": parsed.get("court_id"),
                "docket_number": parsed.get("docket_number"),
                "date_filed": parsed.get("date_filed"),
                "date_terminated": parsed.get("date_terminated"),
                "parties": parsed.get("parties", []),
                "recap_available": parsed.get("recap_available", False),
                "absolute_url": parsed.get("absolute_url"),
                "raw": parsed.get("raw", {}),
                "last_seen_at": now,
                "last_synced_at": now,
            },
        )
        await db.execute(stmt)

    await db.flush()

    # Fetch cached rows for response (with our UUIDs), preserve order
    cache_rows: list[dict[str, Any]] = []
    if ext_ids:
        result = await db.execute(
            select(FederalCaseCache).where(
                FederalCaseCache.source == "courtlistener",
                FederalCaseCache.external_docket_id.in_(ext_ids),
            )
        )
        cached = result.scalars().all()
        cache_by_ext = {c.external_docket_id: c for c in cached}
        for eid in ext_ids:
            if eid in cache_by_ext:
                c = cache_by_ext[eid]
                cache_rows.append({
                    "id": str(c.id),
                    "external_docket_id": c.external_docket_id,
                    "case_name": c.case_name,
                    "docket_number": c.docket_number,
                    "court_id": c.court_id,
                    "date_filed": c.date_filed.isoformat() if c.date_filed else None,
                    "recap_available": c.recap_available,
                    "absolute_url": c.absolute_url,
                    "detected_mode": mode,
                })

    # Log search
    log = FederalCaseSearchLog(
        user_id=current_user.id,
        query=q,
        detected_mode=mode,
    )
    db.add(log)
    await db.flush()

    return {
        "query": q,
        "detected_mode": mode,
        "next_cursor": next_cursor,
        "results": cache_rows,
    }


@router.get("/{case_id}")
async def get_federal_case(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Get cached federal case by UUID. No external call."""
    result = await db.execute(
        select(FederalCaseCache).where(FederalCaseCache.id == case_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "id": str(row.id),
        "external_docket_id": row.external_docket_id,
        "court_id": row.court_id,
        "case_name": row.case_name,
        "docket_number": row.docket_number,
        "date_filed": row.date_filed.isoformat() if row.date_filed else None,
        "date_terminated": row.date_terminated.isoformat() if row.date_terminated else None,
        "parties": row.parties or [],
        "recap_available": row.recap_available,
        "absolute_url": row.absolute_url,
    }


