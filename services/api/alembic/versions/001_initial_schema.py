"""Initial schema with users, cases, shares, documents, audit_logs, opinions, opinion_vectors.

Includes:
- pgvector extension
- GIN index on documents.tsv and opinions.tsv
- IVFFlat index on opinion_vectors.embedding (cosine)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create enum for users (must exist before users table)
    user_role = postgresql.ENUM("attorney", "paralegal", "inmate", name="userrole")
    user_role.create(op.get_bind(), checkfirst=True)

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("attorney", "paralegal", "inmate", name="userrole", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Cases
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cases_created_by_id"), "cases", ["created_by_id"], unique=False)

    # Shares
    op.create_table(
        "shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "user_id", name="uq_share_case_user"),
    )
    op.create_index(op.f("ix_shares_case_id"), "shares", ["case_id"], unique=False)
    op.create_index(op.f("ix_shares_user_id"), "shares", ["user_id"], unique=False)

    # Documents (tsv added as generated column + GIN index)
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("""
        ALTER TABLE documents ADD COLUMN tsv tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
        ) STORED
    """)
    op.create_index("ix_documents_tsv", "documents", ["tsv"], postgresql_using="gin")
    op.create_index(op.f("ix_documents_case_id"), "documents", ["case_id"], unique=False)

    # Audit logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)

    # Opinions (tsv added as generated column + GIN index)
    op.create_table(
        "opinions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("source", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("""
        ALTER TABLE opinions ADD COLUMN tsv tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
        ) STORED
    """)
    op.create_index("ix_opinions_tsv", "opinions", ["tsv"], postgresql_using="gin")
    op.create_index(op.f("ix_opinions_case_id"), "opinions", ["case_id"], unique=False)

    # Opinion vectors (pgvector, IVFFlat for cosine)
    op.execute("""
        CREATE TABLE opinion_vectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            opinion_id UUID NOT NULL REFERENCES opinions(id) ON DELETE CASCADE,
            embedding vector(1536) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.create_index(op.f("ix_opinion_vectors_opinion_id"), "opinion_vectors", ["opinion_id"], unique=False)
    # IVFFlat index for cosine similarity (lists=1 for empty table; run later migration to rebuild with lists=4*sqrt(rows) when populated)
    op.execute("""
        CREATE INDEX ix_opinion_vectors_embedding ON opinion_vectors
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 1)
    """)


def downgrade() -> None:
    op.drop_index("ix_opinion_vectors_embedding", table_name="opinion_vectors")
    op.drop_index(op.f("ix_opinion_vectors_opinion_id"), table_name="opinion_vectors")
    op.drop_table("opinion_vectors")

    op.drop_index("ix_opinions_tsv", table_name="opinions")
    op.drop_index(op.f("ix_opinions_case_id"), table_name="opinions")
    op.drop_table("opinions")

    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_documents_tsv", table_name="documents")
    op.drop_index(op.f("ix_documents_case_id"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_shares_user_id"), table_name="shares")
    op.drop_index(op.f("ix_shares_case_id"), table_name="shares")
    op.drop_table("shares")

    op.drop_index(op.f("ix_cases_created_by_id"), table_name="cases")
    op.drop_table("cases")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP EXTENSION IF EXISTS vector")
