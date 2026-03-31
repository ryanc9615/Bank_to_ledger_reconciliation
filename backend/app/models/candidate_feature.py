from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.match_candidate import MatchCandidate
    from app.models.reconciliation_run import ReconciliationRun


class CandidateFeature(Base):
    __tablename__ = "candidate_features"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    reconciliation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_candidates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    amount_diff_abs: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    amount_match_exact: Mapped[bool] = mapped_column(Boolean, nullable=False)
    currency_match: Mapped[bool] = mapped_column(Boolean, nullable=False)

    date_diff_days_signed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_diff_days_abs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_within_tolerance: Mapped[bool] = mapped_column(Boolean, nullable=False)

    reference_exact_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reference_substring_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reference_similarity: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    reference_missing_warning: Mapped[bool] = mapped_column(Boolean, nullable=False)

    counterparty_exact_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    counterparty_similarity: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)

    description_similarity: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)

    duplicate_amount_count_payment_side: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duplicate_amount_count_bank_side: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duplicate_amount_ambiguity: Mapped[bool] = mapped_column(Boolean, nullable=False)

    reversal_flag_bank: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    match_candidate: Mapped["MatchCandidate"] = relationship(
        "MatchCandidate",
        back_populates="candidate_feature",
    )

    reconciliation_run: Mapped["ReconciliationRun"] = relationship("ReconciliationRun")