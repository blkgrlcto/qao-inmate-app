"""Shared pytest fixtures.

Tests run against a real Postgres database (not sqlite) because the schema
relies on Postgres-specific features (generated tsvector columns, pgvector,
enum types). Point TEST_DATABASE_URL at a throwaway database — defaults to
qao_inmate_test on the same Postgres instance docker-compose brings up.

Each test runs inside a transaction that's rolled back afterward, so tests
never need to clean up after themselves and can run in any order.
"""
import asyncio
import os
import subprocess
import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/qao_inmate_test",
)
# Must be set before any `app.*` module is imported — app.core.config.settings
# and app.db.session.engine are both constructed at import time from this.
os.environ["DB_URL"] = TEST_DB_URL

from app.core.rate_limit import limiter  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """The rate limiter's storage is a process-wide singleton (keyed by
    client IP + route), so without a reset, one test's /auth/login calls
    count toward another test's budget regardless of execution order."""
    limiter.reset()
    yield

API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def _ensure_database_exists() -> None:
    url = make_url(TEST_DB_URL)
    dbname = url.database
    maintenance_url = url.set(database="postgres")
    conn = await asyncpg.connect(
        user=maintenance_url.username,
        password=maintenance_url.password,
        host=maintenance_url.host,
        port=maintenance_url.port or 5432,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Create the test database (if needed) and run migrations once per session."""
    asyncio.run(_ensure_database_exists())
    env = {**os.environ, "DB_URL": TEST_DB_URL}
    subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=API_DIR, env=env)
    yield


@pytest_asyncio.fixture
async def db_session():
    """A session bound to a per-test transaction, rolled back after the test."""
    engine = create_async_engine(TEST_DB_URL)
    connection = await engine.connect()
    transaction = await connection.begin()
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """httpx client against the FastAPI app, with get_db bound to the test transaction."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def make_user(db_session, role: str, email: str | None = None, password: str = "testpass123") -> User:
    """Create and flush a User directly against the test session (bypassing HTTP)."""
    email = email or f"{role}-{uuid.uuid4().hex[:8]}@test.local"
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=f"Test {role.title()}",
        role=role,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def auth_header(user: User) -> dict:
    token = create_access_token(subject=str(user.id), token_version=user.token_version)
    return {"Authorization": f"Bearer {token}"}
