"""Document upload, list, and stream endpoints."""
import io
import uuid
from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.deps import get_current_user, require_roles
from app.models.case import Case, CaseStatus
from app.models.deadline import Deadline
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.share import Share
from app.models.user import User, UserRole
from app.db.session import get_db
from app.services.ai import embed_texts
from app.services.chunking import chunk_text
from app.services.pdf import extract_text_from_pdf
from app.services.s3 import get_object_stream, upload_file

cases_router = APIRouter(prefix="/cases", tags=["cases", "documents"])
files_router = APIRouter(prefix="/files", tags=["files"])
docs_router = APIRouter(prefix="/docs", tags=["documents"])


async def _user_has_case_access(
    db: AsyncSession, user_id: uuid.UUID, case_id: uuid.UUID
) -> bool:
    """Check if user has share on case."""
    result = await db.execute(
        select(Share).where(Share.case_id == case_id, Share.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def _can_access_document(
    db: AsyncSession, user: User, doc: Document
) -> bool:
    """Check share access and inmate_visible for inmates."""
    has_share = await _user_has_case_access(db, user.id, doc.case_id)
    if not has_share:
        return False
    role = user.role if isinstance(user.role, str) else user.role.value
    if role == "inmate" and not doc.inmate_visible:
        return False
    return True


async def _next_deadlines_for_cases(db: AsyncSession, case_ids: list) -> dict:
    """Map case_id -> soonest upcoming (or today's) deadline, as {title, due_date}."""
    if not case_ids:
        return {}
    today = date.today()
    result = await db.execute(
        select(Deadline)
        .where(Deadline.case_id.in_(case_ids), Deadline.due_date >= today)
        .order_by(Deadline.case_id, Deadline.due_date)
    )
    next_by_case = {}
    for d in result.scalars().all():
        if d.case_id not in next_by_case:
            next_by_case[d.case_id] = {"title": d.title, "due_date": d.due_date.isoformat()}
    return next_by_case


@cases_router.get("")
async def list_cases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List cases shared with the current user."""
    result = await db.execute(
        select(Case)
        .join(Share, Share.case_id == Case.id)
        .where(Share.user_id == current_user.id)
        .order_by(Case.updated_at.desc())
    )
    cases = result.scalars().all()
    next_deadlines = await _next_deadlines_for_cases(db, [c.id for c in cases])
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "updated_at": c.updated_at.isoformat(),
            "next_deadline": next_deadlines.get(c.id),
        }
        for c in cases
    ]


@cases_router.post("")
async def create_case(
    title: str = Body(...),
    description: Optional[str] = Body(None),
    current_user: Annotated[User, Depends(require_roles(UserRole.ATTORNEY, UserRole.PARALEGAL))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Create a case. Attorney/paralegal only. Creator is auto-shared as owner."""
    case = Case(title=title, description=description, created_by_id=current_user.id)
    db.add(case)
    await db.flush()

    db.add(Share(case_id=case.id, user_id=current_user.id, role="owner"))
    await db.flush()

    await log_audit(db, current_user.id, "case_create", "case", str(case.id))

    return {
        "id": str(case.id),
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "updated_at": case.updated_at.isoformat(),
    }


@cases_router.get("/{case_id}")
async def get_case(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get case detail. Requires share access."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    next_deadlines = await _next_deadlines_for_cases(db, [case.id])
    return {
        "id": str(case.id),
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "updated_at": case.updated_at.isoformat(),
        "next_deadline": next_deadlines.get(case.id),
    }


@cases_router.patch("/{case_id}")
async def update_case_status(
    case_id: uuid.UUID,
    status: str = Body(..., embed=True),
    current_user: Annotated[User, Depends(require_roles(UserRole.ATTORNEY, UserRole.PARALEGAL))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Update a case's status. Attorney/paralegal with case access only."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")
    if status not in {s.value for s in CaseStatus}:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = status
    await db.flush()

    await log_audit(db, current_user.id, "case_status_update", "case", str(case.id), {"status": status})

    return {"id": str(case.id), "status": case.status}


@cases_router.get("/{case_id}/deadlines")
async def list_deadlines(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List deadlines for a case. Requires share access (read-only for inmates)."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Deadline).where(Deadline.case_id == case_id).order_by(Deadline.due_date)
    )
    deadlines = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "due_date": d.due_date.isoformat(),
            "notes": d.notes,
        }
        for d in deadlines
    ]


@cases_router.post("/{case_id}/deadlines")
async def create_deadline(
    case_id: uuid.UUID,
    title: str = Body(...),
    due_date: date = Body(...),
    notes: Optional[str] = Body(None),
    current_user: Annotated[User, Depends(require_roles(UserRole.ATTORNEY, UserRole.PARALEGAL))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Add a deadline to a case. Attorney/paralegal with case access only."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")

    deadline = Deadline(case_id=case_id, title=title, due_date=due_date, notes=notes)
    db.add(deadline)
    await db.flush()

    await log_audit(db, current_user.id, "deadline_create", "deadline", str(deadline.id))

    return {
        "id": str(deadline.id),
        "title": deadline.title,
        "due_date": deadline.due_date.isoformat(),
        "notes": deadline.notes,
    }


@cases_router.delete("/{case_id}/deadlines/{deadline_id}")
async def delete_deadline(
    case_id: uuid.UUID,
    deadline_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_roles(UserRole.ATTORNEY, UserRole.PARALEGAL))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Remove a deadline from a case. Attorney/paralegal with case access only."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Deadline).where(Deadline.id == deadline_id, Deadline.case_id == case_id)
    )
    deadline = result.scalar_one_or_none()
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")

    await db.delete(deadline)
    await log_audit(db, current_user.id, "deadline_delete", "deadline", str(deadline_id))

    return {"id": str(deadline_id), "deleted": True}


@cases_router.post("/{case_id}/docs")
async def upload_document(
    case_id: uuid.UUID,
    file: UploadFile,
    inmate_visible: bool = False,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Upload a document to a case. PDF text is extracted for search."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")

    content_type = file.content_type or "application/octet-stream"
    data = await file.read()

    content = None
    if content_type == "application/pdf" or file.filename and file.filename.lower().endswith(".pdf"):
        content = extract_text_from_pdf(data)

    key = f"cases/{case_id}/{uuid.uuid4()}/{file.filename or 'document'}"
    upload_file(key, io.BytesIO(data), content_type)

    doc = Document(
        case_id=case_id,
        title=file.filename or "Untitled",
        content=content,
        file_path=key,
        inmate_visible=inmate_visible,
    )
    db.add(doc)
    await db.flush()

    if content:
        chunks = chunk_text(content)
        if chunks:
            embeddings, provider = await embed_texts(chunks)
            for i, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
                db.add(
                    DocumentChunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_content,
                        embedding=embedding,
                        provider=provider,
                    )
                )
            await db.flush()

    await log_audit(db, current_user.id, "document_upload", "document", str(doc.id))

    return {"id": str(doc.id), "title": doc.title, "inmate_visible": doc.inmate_visible}


@cases_router.get("/{case_id}/docs")
async def list_case_documents(
    case_id: uuid.UUID,
    q: Optional[str] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List documents for a case. Use q= for full-text search (ts_rank)."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")

    role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
    is_inmate = role == "inmate"

    if q and q.strip():
        query = text("""
            SELECT d.id, d.title, d.created_at, d.inmate_visible,
                   ts_rank(d.tsv, plainto_tsquery('english', :query)) AS rank
            FROM documents d
            WHERE d.case_id = :case_id
              AND d.tsv @@ plainto_tsquery('english', :query)
              AND (:is_inmate = false OR d.inmate_visible = true)
            ORDER BY rank DESC
        """)
        result = await db.execute(
            query,
            {"case_id": case_id, "query": q.strip(), "is_inmate": is_inmate},
        )
    else:
        if is_inmate:
            result = await db.execute(
                select(Document)
                .where(Document.case_id == case_id, Document.inmate_visible == True)
                .order_by(Document.created_at.desc())
            )
        else:
            result = await db.execute(
                select(Document)
                .where(Document.case_id == case_id)
                .order_by(Document.created_at.desc())
            )
        docs = result.scalars().all()
        return [
            {"id": str(d.id), "title": d.title, "created_at": d.created_at.isoformat(), "inmate_visible": d.inmate_visible}
            for d in docs
        ]

    rows = result.all()
    if q and rows:
        return [
            {
                "id": str(r[0]),
                "title": r[1],
                "created_at": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2]),
                "inmate_visible": r[3],
            }
            for r in rows
        ]
    return []


@docs_router.get("/inmate")
async def list_inmate_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all inmate-visible docs across cases shared with user (for inmate home)."""
    role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
    if role != "inmate":
        raise HTTPException(status_code=403, detail="For inmates only")
    result = await db.execute(
        select(Document, Case.title)
        .join(Case, Case.id == Document.case_id)
        .join(Share, Share.case_id == Document.case_id)
        .where(Share.user_id == current_user.id, Document.inmate_visible == True)
        .order_by(Document.created_at.desc())
    )
    rows = result.all()
    return [
        {"id": str(r[0].id), "title": r[0].title, "case_title": r[1], "case_id": str(r[0].case_id)}
        for r in rows
    ]


@files_router.patch("/{doc_id}")
async def update_document(
    doc_id: uuid.UUID,
    inmate_visible: Optional[bool] = Body(None, embed=True),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Update document (e.g. toggle inmate_visible). Requires case share."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not await _user_has_case_access(db, current_user.id, doc.case_id):
        raise HTTPException(status_code=403, detail="Access denied")
    if inmate_visible is not None:
        doc.inmate_visible = inmate_visible
    await db.flush()
    return {"id": str(doc.id), "inmate_visible": doc.inmate_visible}


@files_router.get("/{doc_id}/stream")
async def stream_file(
    doc_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Stream file content. Enforces case share access and inmate_visible for inmates."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc or not doc.file_path:
        raise HTTPException(status_code=404, detail="Document not found")

    if not await _can_access_document(db, current_user, doc):
        raise HTTPException(status_code=403, detail="Access denied")

    await log_audit(db, current_user.id, "document_download", "document", str(doc.id))

    try:
        body, content_type = get_object_stream(doc.file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found in storage")

    return StreamingResponse(
        body.iter_chunks(chunk_size=8192),
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{doc.title}"'},
    )
