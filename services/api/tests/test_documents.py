"""Document upload/visibility authorization tests.

Upload tests hit real MinIO (via app.services.s3) — the docker-compose MinIO
service must be running, same as for local dev.
"""
from app.models.case import Case
from app.models.document import Document
from app.models.share import Share
from tests.conftest import auth_header, make_user


async def _make_case_with_share(db_session, user, role="editor") -> Case:
    case = Case(title="Doc Test Case", created_by_id=user.id)
    db_session.add(case)
    await db_session.flush()
    db_session.add(Share(case_id=case.id, user_id=user.id, role=role))
    await db_session.flush()
    return case


async def test_upload_requires_case_access(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = Case(title="No Access Case")  # attorney has no share on this case
    db_session.add(case)
    await db_session.flush()

    res = await client.post(
        f"/api/v1/cases/{case.id}/docs",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")},
        headers=auth_header(attorney),
    )

    assert res.status_code == 403


async def test_upload_and_toggle_inmate_visible(client, db_session):
    attorney = await make_user(db_session, "attorney")
    inmate = await make_user(db_session, "inmate")
    case = await _make_case_with_share(db_session, attorney)
    db_session.add(Share(case_id=case.id, user_id=inmate.id, role="viewer"))
    await db_session.flush()

    upload_res = await client.post(
        f"/api/v1/cases/{case.id}/docs?inmate_visible=false",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")},
        headers=auth_header(attorney),
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]
    assert upload_res.json()["inmate_visible"] is False

    # Not yet inmate_visible — inmate's document list should be empty.
    inmate_docs_res = await client.get("/api/v1/docs/inmate", headers=auth_header(inmate))
    assert inmate_docs_res.status_code == 200
    assert inmate_docs_res.json() == []

    # Toggle visible.
    toggle_res = await client.patch(
        f"/api/v1/files/{doc_id}",
        json={"inmate_visible": True},
        headers=auth_header(attorney),
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["inmate_visible"] is True

    inmate_docs_res = await client.get("/api/v1/docs/inmate", headers=auth_header(inmate))
    assert inmate_docs_res.status_code == 200
    assert [d["id"] for d in inmate_docs_res.json()] == [doc_id]


async def test_inmate_document_list_excludes_non_visible_docs(client, db_session):
    attorney = await make_user(db_session, "attorney")
    inmate = await make_user(db_session, "inmate")
    case = await _make_case_with_share(db_session, attorney)
    db_session.add(Share(case_id=case.id, user_id=inmate.id, role="viewer"))
    await db_session.flush()

    visible_doc = Document(case_id=case.id, title="Visible", inmate_visible=True)
    hidden_doc = Document(case_id=case.id, title="Hidden", inmate_visible=False)
    db_session.add_all([visible_doc, hidden_doc])
    await db_session.flush()

    res = await client.get(f"/api/v1/cases/{case.id}/docs", headers=auth_header(inmate))

    assert res.status_code == 200
    titles = [d["title"] for d in res.json()]
    assert titles == ["Visible"]
