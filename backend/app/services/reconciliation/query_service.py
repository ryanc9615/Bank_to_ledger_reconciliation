from __future__ import annotations

from sqlalchemy import and_, not_, select
from sqlalchemy.orm import Session

from app.models.bank_transaction import BankTransaction
from app.models.candidate_feature import CandidateFeature
from app.models.match_candidate import MatchCandidate
from app.models.match_decision import MatchDecision
from app.models.payment_record import PaymentRecord
from app.models.reconciliation_run import ReconciliationRun


class QueueTypeError(ValueError):
    pass


class ProposalNotFoundError(LookupError):
    pass


class RunNotFoundError(LookupError):
    pass


class ReconciliationQueryService:
    SUPPORTED_QUEUE_TYPES = {
        "auto_matched",
        "review",
        "unmatched_payments",
        "unmatched_bank",
        "deferred",
    }

    def list_runs(self, db: Session) -> list[ReconciliationRun]:
        return list(
            db.execute(
                select(ReconciliationRun).order_by(ReconciliationRun.started_at.desc())
            ).scalars().all()
        )

    def get_run(self, db: Session, run_id) -> ReconciliationRun:
        run = db.execute(
            select(ReconciliationRun).where(ReconciliationRun.id == run_id)
        ).scalar_one_or_none()

        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")

        return run

    def list_run_proposals(
        self,
        db: Session,
        run_id,
        selected_only: bool = True,
    ) -> list[MatchCandidate]:
        self.get_run(db, run_id)

        stmt = select(MatchCandidate).where(
            MatchCandidate.reconciliation_run_id == run_id
        )

        if selected_only:
            stmt = stmt.where(MatchCandidate.is_selected_match.is_(True))

        stmt = stmt.order_by(MatchCandidate.raw_score.desc())

        return list(db.execute(stmt).scalars().all())

    def get_proposal_detail(self, db: Session, run_id, candidate_id):
        self.get_run(db, run_id)

        candidate = db.execute(
            select(MatchCandidate).where(
                MatchCandidate.reconciliation_run_id == run_id,
                MatchCandidate.id == candidate_id,
            )
        ).scalar_one_or_none()

        if candidate is None:
            raise ProposalNotFoundError(
                f"Proposal {candidate_id} not found for run {run_id}"
            )

        payment = db.execute(
            select(PaymentRecord).where(PaymentRecord.id == candidate.payment_record_id)
        ).scalar_one_or_none()

        bank = db.execute(
            select(BankTransaction).where(BankTransaction.id == candidate.bank_transaction_id)
        ).scalar_one_or_none()

        if payment is None or bank is None:
            raise ProposalNotFoundError(
                f"Proposal {candidate_id} exists but linked records are missing"
            )

        feature = db.execute(
            select(CandidateFeature).where(CandidateFeature.match_candidate_id == candidate.id)
        ).scalar_one_or_none()

        alternatives = list(
            db.execute(
                select(MatchCandidate).where(
                    MatchCandidate.reconciliation_run_id == run_id,
                    MatchCandidate.payment_record_id == candidate.payment_record_id,
                    MatchCandidate.id != candidate.id,
                ).order_by(MatchCandidate.raw_score.desc())
            ).scalars().all()
        )

        current_decision = db.execute(
            select(MatchDecision).where(
                MatchDecision.run_id == run_id,
                MatchDecision.payment_record_id == candidate.payment_record_id,
                MatchDecision.is_active.is_(True),
            )
        ).scalar_one_or_none()

        return candidate, payment, bank, feature, alternatives, current_decision

    def get_queue_items(self, db: Session, run_id, queue_type: str):
        self.get_run(db, run_id)

        if queue_type not in self.SUPPORTED_QUEUE_TYPES:
            raise QueueTypeError(f"Unsupported queue type: {queue_type}")

        if queue_type == "auto_matched":
            return self._selected_candidates_by_route(db, run_id, "auto_match")

        if queue_type == "review":
            return self._selected_candidates_by_route(db, run_id, "review")

        if queue_type == "unmatched_payments":
            return self._unmatched_payments(db, run_id)

        if queue_type == "unmatched_bank":
            return self._unmatched_bank(db, run_id)

        if queue_type == "deferred":
            return self._deferred_items(db, run_id)

        raise QueueTypeError(f"Unsupported queue type: {queue_type}")

    def _selected_candidates_by_route(
        self,
        db: Session,
        run_id,
        route_status: str,
    ) -> list[MatchCandidate]:
        return list(
            db.execute(
                select(MatchCandidate).where(
                    MatchCandidate.reconciliation_run_id == run_id,
                    MatchCandidate.is_selected_match.is_(True),
                    MatchCandidate.route_status == route_status,
                ).order_by(MatchCandidate.raw_score.desc())
            ).scalars().all()
        )

    def _unmatched_payments(self, db: Session, run_id) -> list[PaymentRecord]:
        matched_payment_ids = select(MatchCandidate.payment_record_id).where(
            MatchCandidate.reconciliation_run_id == run_id,
            MatchCandidate.is_selected_match.is_(True),
        )

        return list(
            db.execute(
                select(PaymentRecord).where(
                    not_(PaymentRecord.id.in_(matched_payment_ids))
                )
            ).scalars().all()
        )

    def _unmatched_bank(self, db: Session, run_id) -> list[BankTransaction]:
        matched_bank_ids = select(MatchCandidate.bank_transaction_id).where(
            MatchCandidate.reconciliation_run_id == run_id,
            MatchCandidate.is_selected_match.is_(True),
        )

        return list(
            db.execute(
                select(BankTransaction).where(
                    and_(
                        BankTransaction.direction == "credit",
                        BankTransaction.is_reversal.is_(False),
                        not_(BankTransaction.id.in_(matched_bank_ids)),
                    )
                )
            ).scalars().all()
        )

    def _deferred_items(self, db: Session, run_id) -> list[MatchDecision]:
        return list(
            db.execute(
                select(MatchDecision).where(
                    MatchDecision.run_id == run_id,
                    MatchDecision.is_active.is_(True),
                    MatchDecision.decision_status == "deferred",
                ).order_by(MatchDecision.created_at.desc())
            ).scalars().all()
        )