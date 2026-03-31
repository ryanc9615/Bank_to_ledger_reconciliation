from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.match_candidate import MatchCandidate


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parameters_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_matched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unmatched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    match_candidates: Mapped[list["MatchCandidate"]] = relationship(
        "MatchCandidate",
        back_populates="reconciliation_run",
        cascade="all, delete-orphan",
    )