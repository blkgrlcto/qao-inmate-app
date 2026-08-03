"""Grounded Q&A (RAG) over case documents."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.documents import _user_has_case_access
from app.core.audit import log_audit
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.ai import embed_query, generate_answer

ai_router = APIRouter(prefix="/ai", tags=["ai"])

TOP_K = 5


@ai_router.post("/ask")
async def ask(
    case_id: uuid.UUID = Body(...),
    question: str = Body(..., min_length=1),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Ask a grounded question over a case's uploaded (and indexed) documents.
    Requires case share access; inmates only get matches from inmate_visible
    documents, same access shape as the rest of the documents API."""
    if not await _user_has_case_access(db, current_user.id, case_id):
        raise HTTPException(status_code=403, detail="Access denied")

    role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
    is_inmate = role == "inmate"

    query_embedding, embed_provider = await embed_query(question)

    query = (
        select(DocumentChunk, Document.title, Document.id)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.case_id == case_id)
    )
    if is_inmate:
        query = query.where(Document.inmate_visible.is_(True))
    query = query.order_by(DocumentChunk.embedding.cosine_distance(query_embedding)).limit(TOP_K)

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        await log_audit(
            db, current_user.id, "ai_ask", "case", str(case_id),
            {"question": question, "provider": embed_provider, "num_chunks": 0},
        )
        return {
            "answer": "No documents have been indexed for this case yet.",
            "citations": [],
            "provider": embed_provider,
        }

    chunks = [
        {
            "document_id": str(doc_id),
            "document_title": title,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk, title, doc_id in rows
    ]

    result_ai = await generate_answer(question, chunks)

    await log_audit(
        db, current_user.id, "ai_ask", "case", str(case_id),
        {"question": question, "provider": result_ai["provider"], "num_chunks": len(chunks)},
    )

    return {
        "answer": result_ai["answer"],
        "citations": [
            {
                "document_id": c["document_id"],
                "document_title": c["document_title"],
                "chunk_index": c["chunk_index"],
                "snippet": c["content"][:300],
            }
            for c in chunks
        ],
        "provider": result_ai["provider"],
    }
