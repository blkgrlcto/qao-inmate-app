#!/usr/bin/env python3
"""Seed database with demo data: 1 attorney, 1 paralegal, 1 inmate, 1 demo case shared to all."""
import asyncio
import uuid

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.models.case import Case
from app.models.share import Share
from app.models.user import User


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role: str,
) -> User:
    """Create a user and return it."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


async def seed() -> None:
    """Run seed: create 1 attorney, 1 paralegal, 1 inmate, 1 demo case shared to all.
    
    Run after: alembic upgrade head
    """
    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Create users
        attorney = await create_user(
            session,
            email="attorney@demo.local",
            password="demo123",
            full_name="Demo Attorney",
            role="attorney",
        )
        paralegal = await create_user(
            session,
            email="paralegal@demo.local",
            password="demo123",
            full_name="Demo Paralegal",
            role="paralegal",
        )
        inmate = await create_user(
            session,
            email="inmate@demo.local",
            password="demo123",
            full_name="Demo Inmate",
            role="inmate",
        )
        await session.flush()

        # Create demo case
        demo_case = Case(
            id=uuid.uuid4(),
            title="Demo Case",
            description="A sample case for demonstration purposes.",
            status="open",
            created_by_id=attorney.id,
        )
        session.add(demo_case)
        await session.flush()

        # Share case to all three users
        for user in (attorney, paralegal, inmate):
            share = Share(
                id=uuid.uuid4(),
                case_id=demo_case.id,
                user_id=user.id,
                role="viewer" if user.role == "inmate" else "editor",
            )
            session.add(share)

        await session.commit()
        print("Seed complete: 1 attorney, 1 paralegal, 1 inmate, 1 demo case shared to all.")
        print("  attorney@demo.local / demo123")
        print("  paralegal@demo.local / demo123")
        print("  inmate@demo.local / demo123")


if __name__ == "__main__":
    asyncio.run(seed())
