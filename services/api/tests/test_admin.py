"""Admin-only endpoint authorization tests."""
from app.models.case import Case
from tests.conftest import auth_header, make_user


async def test_non_admin_cannot_create_user(client, db_session):
    attorney = await make_user(db_session, "attorney")

    res = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "sneaky@test.local",
            "password": "whatever123",
            "full_name": "Sneaky",
            "role": "admin",
        },
        headers=auth_header(attorney),
    )

    assert res.status_code == 403


async def test_admin_can_create_and_list_user(client, db_session):
    admin = await make_user(db_session, "admin")

    create_res = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "new-attorney@test.local",
            "password": "whatever123",
            "full_name": "New Attorney",
            "role": "attorney",
        },
        headers=auth_header(admin),
    )
    assert create_res.status_code == 200
    assert "hashed_password" not in create_res.json()
    new_user_id = create_res.json()["id"]

    list_res = await client.get("/api/v1/admin/users", headers=auth_header(admin))
    assert list_res.status_code == 200
    assert any(u["id"] == new_user_id for u in list_res.json())


async def test_admin_can_grant_case_access(client, db_session):
    admin = await make_user(db_session, "admin")
    attorney = await make_user(db_session, "attorney")
    case = Case(title="Admin-Managed Case")
    db_session.add(case)
    await db_session.flush()

    res = await client.post(
        "/api/v1/admin/shares",
        json={"case_id": str(case.id), "user_id": str(attorney.id), "role": "viewer"},
        headers=auth_header(admin),
    )

    assert res.status_code == 200

    shares_res = await client.get(
        f"/api/v1/admin/shares?case_id={case.id}", headers=auth_header(admin)
    )
    assert shares_res.status_code == 200
    assert [s["user_id"] for s in shares_res.json()] == [str(attorney.id)]
