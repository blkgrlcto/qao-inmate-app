"""Opinion vector model for semantic search (pgvector)."""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Embedding dimension (e.g., OpenAI text-embedding-3-small=1536, ada-002=1536)
EMBEDDING_DIM = 1536


class OpinionVector(Base):
    """Vector embedding for opinion semantic search."""

    __tablename__ = "opinion_vectors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    opinion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opinions.id", ondelete="CASCADE"), nullable=False
    )
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    opinion = relationship("Opinion", back_populates="vectors")
