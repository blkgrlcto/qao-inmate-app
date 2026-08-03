"""Add document_chunks table for RAG grounded Q&A over case documents."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_document_chunks"
down_revision: Union[str, Sequence[str], None] = "007_case_status_and_deadlines"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            provider VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.create_index(
        "ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False
    )
    # IVFFlat index for cosine similarity — lists=1 is the right default for an
    # empty table; rebuild with lists=4*sqrt(rows) once real data exists (same
    # note as opinion_vectors in migration 001).
    op.execute("""
        CREATE INDEX ix_document_chunks_embedding ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 1)
    """)


def downgrade() -> None:
    op.drop_index("ix_document_chunks_embedding", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")
