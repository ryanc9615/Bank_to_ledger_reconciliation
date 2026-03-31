from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.bank_transaction import BankTransaction
    from app.models.payment_record import PaymentRecord
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.candidate_feature import CandidateFeature


class MatchCandidate(Base):
    __tablename__ = "match_candidates"

    __table_args__ = (
        UniqueConstraint(
            "reconciliation_run_id",
            "payment_record_id",
            "bank_transaction_id",
            name="uq_match_candidate_run_payment_bank",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    reconciliation_run_id: Mapped[uuid.UUID] = mapped_column(
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

    bank_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bank_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    block_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    raw_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)

    score_reasons_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    score_warnings_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    guardrail_flags_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    auto_match_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assignment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    route_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_selected_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rank_for_payment: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_for_bank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    score_gap_to_next_payment_candidate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    score_gap_to_next_bank_candidate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reconciliation_run: Mapped["ReconciliationRun"] = relationship(
        "ReconciliationRun",
        back_populates="match_candidates",
    )

    payment_record: Mapped["PaymentRecord"] = relationship("PaymentRecord")
    bank_transaction: Mapped["BankTransaction"] = relationship("BankTransaction")

    candidate_feature: Mapped["CandidateFeature | None"] = relationship(
        "CandidateFeature",
        back_populates="match_candidate",
        cascade="all, delete-orphan",
        uselist=False,
    )