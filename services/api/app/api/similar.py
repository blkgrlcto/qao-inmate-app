"""Similar case search — full-text search (tsvector/ts_rank) over the opinions
precedent table. Any authenticated role may search."""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User

similar_router = APIRouter(prefix="/similar", tags=["similar"])


@similar_router.get("")
async def search_similar(
    q: str = Query(..., min_length=1),
    jurisdiction: Optional[str] = Query(None),
    disposition: Optional[List[str]] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Keyword full-text search over opinions.tsv. Not semantic similarity —
    that requires embeddings (tracked separately)."""
    conditions = ["tsv @@ plainto_tsquery('english', :query)"]
    params: dict = {"query": q, "limit": limit}

    if jurisdiction:
        conditions.append("jurisdiction = :jurisdiction")
        params["jurisdiction"] = jurisdiction

    if disposition:
        placeholders = []
        for i, d in enumerate(disposition):
            key = f"disposition_{i}"
            placeholders.append(f":{key}")
            params[key] = d
        conditions.append(f"disposition IN ({', '.join(placeholders)})")

    where_clause = " AND ".join(conditions)
    query = text(f"""
        SELECT id, citation, title, jurisdiction, disposition, headline, pull_quotes,
               source, date_decided,
               ts_rank(tsv, plainto_tsquery('english', :query)) AS rank
        FROM opinions
        WHERE {where_clause}
        ORDER BY rank DESC
        LIMIT :limit
    """)
    result = await db.execute(query, params)
    rows = result.all()

    return {
        "query": q,
        "results": [
            {
                "id": str(r.id),
                "citation": r.citation or "",
                "title": r.title,
                "jurisdiction": r.jurisdiction or "",
                "date": r.date_decided.isoformat() if r.date_decided else "",
                "disposition": r.disposition or "",
                "score": float(r.rank),
                "headline": r.headline,
                "pull_quotes": r.pull_quotes,
                "source_url": r.source,
            }
            for r in rows
        ],
    }
