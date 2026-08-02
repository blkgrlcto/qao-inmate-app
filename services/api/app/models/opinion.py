"""Opinion model with full-text search (tsvector).

Opinions are either attached to a specific case (case_id set) or are global
precedent entries (case_id NULL) used by full-text "similar case" search.
"""
import uuid
from datetime import date as date_type, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Opinion(Base):
    """Legal opinion with tsvector for full-text search."""

    __tablename__ = "opinions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    citation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    disposition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pull_quotes: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    date_decided: Mapped[Optional[date_type]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    case = relationship("Case", back_populates="opinions")
    vectors = relationship("OpinionVector", back_populates="opinion", cascade="all, delete-orphan")
