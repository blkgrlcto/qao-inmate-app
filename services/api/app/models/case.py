"""Case model."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CaseStatus(str, enum.Enum):
    """Case status enumeration."""

    OPEN = "open"
    ACTIVE = "active"
    AWAITING_DECISION = "awaiting_decision"
    CLOSED = "closed"


class Case(Base):
    """Legal case."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(CaseStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CaseStatus.OPEN,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by_user = relationship("User", back_populates="cases_created")
    shares = relationship("Share", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    opinions = relationship("Opinion", back_populates="case", cascade="all, delete-orphan")
    deadlines = relationship(
        "Deadline", back_populates="case", cascade="all, delete-orphan", order_by="Deadline.due_date"
    )
