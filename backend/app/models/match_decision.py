from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MatchDecision(Base):
    __tablename__ = "match_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    payment_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    bank_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bank_transactions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    match_candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_candidates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    decision_action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    decision_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    reviewer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_reason_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    evidence_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    superseded_by_decision_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_decisions.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    run = relationship("ReconciliationRun")
    candidate = relationship("MatchCandidate", foreign_keys=[match_candidate_id])