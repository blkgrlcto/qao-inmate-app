"""Full-text search over the opinions precedent table."""
from app.models.opinion import Opinion
from tests.conftest import auth_header, make_user


async def _seed_opinion(db_session, **overrides):
    defaults = dict(
        case_id=None,
        title="Sample v. Precedent",
        content="A case about ineffective assistance of counsel and habeas corpus appeals.",
        citation="1 T.S. 1 (2000)",
        jurisdiction="US",
        disposition="REVERSED",
    )
    defaults.update(overrides)
    opinion = Opinion(**defaults)
    db_session.add(opinion)
    await db_session.flush()
    return opinion


async def test_similar_search_returns_matching_opinion(client, db_session):
    inmate = await make_user(db_session, "inmate")
    await _seed_opinion(db_session)
    await _seed_opinion(
        db_session,
        title="Unrelated Tax Dispute",
        content="A case entirely about property tax assessment appeals.",
    )

    res = await client.get(
        "/api/v1/similar", params={"q": "ineffective assistance of counsel"}, headers=auth_header(inmate)
    )

    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Sample v. Precedent"
    assert results[0]["citation"] == "1 T.S. 1 (2000)"


async def test_similar_search_no_match_returns_empty_list(client, db_session):
    inmate = await make_user(db_session, "inmate")
    await _seed_opinion(db_session)

    res = await client.get(
        "/api/v1/similar",
        params={"q": "zzzznonexistentquerytermzzzz"},
        headers=auth_header(inmate),
    )

    assert res.status_code == 200
    assert res.json()["results"] == []
