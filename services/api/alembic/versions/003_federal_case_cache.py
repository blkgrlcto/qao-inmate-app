"""Federal case cache and search log for CourtListener integration."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_federal_case_cache"
down_revision: Union[str, Sequence[str], None] = "002_add_document_inmate_visible"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # federal_case_cache
    op.create_table(
        "federal_case_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(64), nullable=False, server_default="courtlistener"),
        sa.Column("external_docket_id", sa.BigInteger(), nullable=False),
        sa.Column("court_id", sa.String(64), nullable=True),
        sa.Column("case_name", sa.String(1024), nullable=True),
        sa.Column("docket_number", sa.String(128), nullable=True),
        sa.Column("date_filed", sa.Date(), nullable=True),
        sa.Column("date_terminated", sa.Date(), nullable=True),
        sa.Column("parties", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("recap_available", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("absolute_url", sa.String(2048), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_docket_id", name="uq_federal_case_cache_source_ext"),
    )
    op.create_index("ix_federal_case_cache_docket_number", "federal_case_cache", ["docket_number"])
    op.create_index("ix_federal_case_cache_court_id", "federal_case_cache", ["court_id"])
    op.create_index("ix_federal_case_cache_last_seen_at", "federal_case_cache", ["last_seen_at"])

    # federal_case_search_log
    op.create_table(
        "federal_case_search_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("detected_mode", sa.String(16), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_federal_case_search_log_user_id", "federal_case_search_log", ["user_id"])
    op.create_index("ix_federal_case_search_log_at", "federal_case_search_log", ["at"])


def downgrade() -> None:
    op.drop_index("ix_federal_case_search_log_at", table_name="federal_case_search_log")
    op.drop_index("ix_federal_case_search_log_user_id", table_name="federal_case_search_log")
    op.drop_table("federal_case_search_log")

    op.drop_index("ix_federal_case_cache_last_seen_at", table_name="federal_case_cache")
    op.drop_index("ix_federal_case_cache_court_id", table_name="federal_case_cache")
    op.drop_index("ix_federal_case_cache_docket_number", table_name="federal_case_cache")
    op.drop_table("federal_case_cache")
