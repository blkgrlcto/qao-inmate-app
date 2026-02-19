"""Federal case cache model (CourtListener sync)."""
import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FederalCaseCache(Base):
    """Cached federal docket from CourtListener."""

    __tablename__ = "federal_case_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="courtlistener")
    external_docket_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    court_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    case_name: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    docket_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    date_filed: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_terminated: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    parties: Mapped[list] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    recap_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    absolute_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
