"""Make opinions.case_id nullable and add precedent fields for /similar search.

Global precedent entries (used for full-text "similar case" search) have
case_id = NULL; per-case opinions keep case_id set.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_opinion_precedent_fields"
down_revision: Union[str, Sequence[str], None] = "004_add_admin_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("opinions", "case_id", nullable=True)
    op.add_column("opinions", sa.Column("citation", sa.String(255), nullable=True))
    op.add_column("opinions", sa.Column("jurisdiction", sa.String(50), nullable=True))
    op.add_column("opinions", sa.Column("disposition", sa.String(50), nullable=True))
    op.add_column("opinions", sa.Column("headline", sa.Text(), nullable=True))
    op.add_column(
        "opinions",
        sa.Column("pull_quotes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("opinions", sa.Column("date_decided", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("opinions", "date_decided")
    op.drop_column("opinions", "pull_quotes")
    op.drop_column("opinions", "headline")
    op.drop_column("opinions", "disposition")
    op.drop_column("opinions", "jurisdiction")
    op.drop_column("opinions", "citation")
    op.alter_column("opinions", "case_id", nullable=False)
