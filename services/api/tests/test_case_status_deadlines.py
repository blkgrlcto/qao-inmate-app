"""Case status updates and deadline CRUD authorization."""
from app.models.case import Case
from app.models.share import Share
from tests.conftest import auth_header, make_user


async def _case_with_share(db_session, user, role="editor") -> Case:
    case = Case(title="Status/Deadline Test Case", created_by_id=user.id)
    db_session.add(case)
    await db_session.flush()
    db_session.add(Share(case_id=case.id, user_id=user.id, role=role))
    await db_session.flush()
    return case


async def test_attorney_can_update_status_with_case_access(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, attorney)

    res = await client.patch(
        f"/api/v1/cases/{case.id}", json={"status": "active"}, headers=auth_header(attorney)
    )

    assert res.status_code == 200
    assert res.json()["status"] == "active"


async def test_update_status_403_without_case_access(client, db_session):
    attorney = await make_user(db_session, "attorney")
    other_attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, other_attorney)

    res = await client.patch(
        f"/api/v1/cases/{case.id}", json={"status": "active"}, headers=auth_header(attorney)
    )

    assert res.status_code == 403


async def test_update_status_rejects_invalid_value(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, attorney)

    res = await client.patch(
        f"/api/v1/cases/{case.id}", json={"status": "not-a-real-status"}, headers=auth_header(attorney)
    )

    assert res.status_code == 400


async def test_inmate_cannot_update_status(client, db_session):
    inmate = await make_user(db_session, "inmate")
    case = await _case_with_share(db_session, inmate, role="viewer")

    res = await client.patch(
        f"/api/v1/cases/{case.id}", json={"status": "closed"}, headers=auth_header(inmate)
    )

    assert res.status_code == 403


async def test_deadline_create_list_delete(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, attorney)

    create_res = await client.post(
        f"/api/v1/cases/{case.id}/deadlines",
        json={"title": "File appeal", "due_date": "2030-01-15", "notes": "before deadline"},
        headers=auth_header(attorney),
    )
    assert create_res.status_code == 200
    deadline_id = create_res.json()["id"]

    list_res = await client.get(f"/api/v1/cases/{case.id}/deadlines", headers=auth_header(attorney))
    assert list_res.status_code == 200
    assert [d["id"] for d in list_res.json()] == [deadline_id]

    delete_res = await client.delete(
        f"/api/v1/cases/{case.id}/deadlines/{deadline_id}", headers=auth_header(attorney)
    )
    assert delete_res.status_code == 200

    list_res_after = await client.get(f"/api/v1/cases/{case.id}/deadlines", headers=auth_header(attorney))
    assert list_res_after.json() == []


async def test_deadline_requires_case_access(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = Case(title="No Access")
    db_session.add(case)
    await db_session.flush()

    res = await client.post(
        f"/api/v1/cases/{case.id}/deadlines",
        json={"title": "File appeal", "due_date": "2030-01-15"},
        headers=auth_header(attorney),
    )

    assert res.status_code == 403


async def test_inmate_can_read_but_not_create_deadlines(client, db_session):
    inmate = await make_user(db_session, "inmate")
    case = await _case_with_share(db_session, inmate, role="viewer")

    read_res = await client.get(f"/api/v1/cases/{case.id}/deadlines", headers=auth_header(inmate))
    assert read_res.status_code == 200

    create_res = await client.post(
        f"/api/v1/cases/{case.id}/deadlines",
        json={"title": "File appeal", "due_date": "2030-01-15"},
        headers=auth_header(inmate),
    )
    assert create_res.status_code == 403


async def test_list_cases_includes_status_and_next_deadline(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _case_with_share(db_session, attorney)
    await client.post(
        f"/api/v1/cases/{case.id}/deadlines",
        json={"title": "Hearing", "due_date": "2030-06-01"},
        headers=auth_header(attorney),
    )

    res = await client.get("/api/v1/cases", headers=auth_header(attorney))

    assert res.status_code == 200
    row = next(c for c in res.json() if c["id"] == str(case.id))
    assert row["status"] == "open"
    assert row["next_deadline"] == {"title": "Hearing", "due_date": "2030-06-01"}
