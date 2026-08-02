"""Login and current-user auth tests."""
from tests.conftest import auth_header, make_user


async def test_login_success(client, db_session):
    await make_user(db_session, "attorney", email="login-ok@test.local", password="correct-horse")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "login-ok@test.local", "password": "correct-horse"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password(client, db_session):
    await make_user(db_session, "attorney", email="login-bad@test.local", password="correct-horse")

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "login-bad@test.local", "password": "wrong-password"},
    )

    assert res.status_code == 401


async def test_login_unknown_user(client):
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@test.local", "password": "whatever"},
    )

    assert res.status_code == 401


async def test_me_with_valid_token(client, db_session):
    user = await make_user(db_session, "inmate", email="me-ok@test.local")

    res = await client.get("/api/v1/auth/me", headers=auth_header(user))

    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "me-ok@test.local"


async def test_me_without_token(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


async def test_me_with_invalid_token(client):
    res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert res.status_code == 401
