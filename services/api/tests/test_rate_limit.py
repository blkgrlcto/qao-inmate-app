"""Login rate limiting."""
from tests.conftest import make_user


async def test_login_rate_limited_after_five_attempts(client, db_session):
    await make_user(db_session, "attorney", email="rate-limit@test.local", password="correct-horse")

    statuses = []
    for _ in range(6):
        res = await client.post(
            "/api/v1/auth/login",
            data={"username": "rate-limit@test.local", "password": "wrong-password"},
        )
        statuses.append(res.status_code)

    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429
