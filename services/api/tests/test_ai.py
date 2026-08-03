"""Grounded Q&A (RAG) — mock mode only; no live OpenAI calls in tests by design."""
from app.models.case import Case
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.share import Share
from app.services.ai.mock import mock_embed
from app.services.chunking import chunk_text
from tests.conftest import auth_header, make_user


async def _case_with_share(db_session, user, role="editor") -> Case:
    case = Case(title="AI Test Case", created_by_id=user.id)
    db_session.add(case)
    await db_session.flush()
    db_session.add(Share(case_id=case.id, user_id=user.id, role=role))
    await db_session.flush()
    return case


async def _add_chunk(db_session, document: Document, content: str, index: int = 0):
    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=index,
        content=content,
        embedding=mock_embed(content),
        provider="mock",
    )
    db_session.add(chunk)
    await db_session.flush()
    return chunk


async def test_ask_returns_grounded_answer_with_citations(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, attorney)

    relevant_doc = Document(case_id=case.id, title="Sentencing Order", content="...")
    unrelated_doc = Document(case_id=case.id, title="Cover Letter", content="...")
    db_session.add_all([relevant_doc, unrelated_doc])
    await db_session.flush()

    await _add_chunk(
        db_session, relevant_doc,
        "The defendant's sentencing hearing is scheduled for October 1 2026 in courtroom 4B.",
    )
    await _add_chunk(db_session, unrelated_doc, "Dear counsel, please find enclosed the requested forms.")

    res = await client.post(
        "/api/v1/ai/ask",
        json={"case_id": str(case.id), "question": "When is the sentencing hearing?"},
        headers=auth_header(attorney),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["provider"] == "mock"
    assert "sentencing hearing" in body["answer"].lower()
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["document_title"] == "Sentencing Order"


async def test_ask_requires_case_access(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = Case(title="No Access Case")
    db_session.add(case)
    await db_session.flush()

    res = await client.post(
        "/api/v1/ai/ask",
        json={"case_id": str(case.id), "question": "Anything?"},
        headers=auth_header(attorney),
    )

    assert res.status_code == 403


async def test_ask_no_documents_indexed_yet(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, attorney)

    res = await client.post(
        "/api/v1/ai/ask",
        json={"case_id": str(case.id), "question": "Anything?"},
        headers=auth_header(attorney),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["citations"] == []
    assert "no documents" in body["answer"].lower() or "not been indexed" in body["answer"].lower()


async def test_inmate_only_sees_inmate_visible_chunks(client, db_session):
    inmate = await make_user(db_session, "inmate")
    case = await _case_with_share(db_session, inmate, role="viewer")

    visible_doc = Document(case_id=case.id, title="Visible Order", content="...", inmate_visible=True)
    hidden_doc = Document(case_id=case.id, title="Hidden Notes", content="...", inmate_visible=False)
    db_session.add_all([visible_doc, hidden_doc])
    await db_session.flush()

    await _add_chunk(db_session, visible_doc, "Your parole eligibility date is January 5 2027.")
    await _add_chunk(db_session, hidden_doc, "Attorney strategy notes: do not share with client.")

    res = await client.post(
        "/api/v1/ai/ask",
        json={"case_id": str(case.id), "question": "When is my parole eligibility date?"},
        headers=auth_header(inmate),
    )

    assert res.status_code == 200
    titles = [c["document_title"] for c in res.json()["citations"]]
    assert "Hidden Notes" not in titles


def test_chunk_text_splits_with_overlap():
    text = "word " * 1000  # well over the default chunk size
    chunks = chunk_text(text, size=1500, overlap=200)

    assert len(chunks) > 1
    assert all(len(c) <= 1500 for c in chunks)


def test_chunk_text_short_input_returns_single_chunk():
    assert chunk_text("short text", size=1500, overlap=200) == ["short text"]


def test_chunk_text_empty_input_returns_no_chunks():
    assert chunk_text("   ", size=1500, overlap=200) == []
