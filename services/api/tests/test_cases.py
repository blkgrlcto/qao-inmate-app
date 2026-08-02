"""Case list/get/create authorization tests."""
from app.models.case import Case
from app.models.share import Share
from tests.conftest import auth_header, make_user


async def _make_case(db_session, title="Test Case", created_by=None) -> Case:
    case = Case(title=title, created_by_id=created_by.id if created_by else None)
    db_session.add(case)
    await db_session.flush()
    return case


async def _share(db_session, case: Case, user, role="viewer"):
    db_session.add(Share(case_id=case.id, user_id=user.id, role=role))
    await db_session.flush()


async def test_list_cases_only_returns_shared_cases(client, db_session):
    attorney = await make_user(db_session, "attorney")
    shared_case = await _make_case(db_session, title="Shared With Me", created_by=attorney)
    await _share(db_session, shared_case, attorney)
    await _make_case(db_session, title="Not Shared")  # no share for `attorney`

    res = await client.get("/api/v1/cases", headers=auth_header(attorney))

    assert res.status_code == 200
    titles = [c["title"] for c in res.json()]
    assert titles == ["Shared With Me"]


async def test_get_case_403_without_share(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _make_case(db_session, title="Someone Else's Case")

    res = await client.get(f"/api/v1/cases/{case.id}", headers=auth_header(attorney))

    assert res.status_code == 403


async def test_get_case_ok_with_share(client, db_session):
    attorney = await make_user(db_session, "attorney")
    case = await _make_case(db_session, title="My Case", created_by=attorney)
    await _share(db_session, case, attorney)

    res = await client.get(f"/api/v1/cases/{case.id}", headers=auth_header(attorney))

    assert res.status_code == 200
    assert res.json()["title"] == "My Case"


async def test_attorney_can_create_case_and_see_it_immediately(client, db_session):
    attorney = await make_user(db_session, "attorney")

    create_res = await client.post(
        "/api/v1/cases",
        json={"title": "New Case", "description": "Created via API"},
        headers=auth_header(attorney),
    )
    assert create_res.status_code == 200
    case_id = create_res.json()["id"]

    list_res = await client.get("/api/v1/cases", headers=auth_header(attorney))
    assert list_res.status_code == 200
    assert any(c["id"] == case_id for c in list_res.json())


async def test_inmate_cannot_create_case(client, db_session):
    inmate = await make_user(db_session, "inmate")

    res = await client.post(
        "/api/v1/cases",
        json={"title": "Should Not Be Created"},
        headers=auth_header(inmate),
    )

    assert res.status_code == 403
