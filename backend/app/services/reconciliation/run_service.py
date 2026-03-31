from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.bank_transaction import BankTransaction
from app.models.candidate_feature import CandidateFeature
from app.models.match_candidate import MatchCandidate
from app.models.payment_record import PaymentRecord
from app.models.reconciliation_run import ReconciliationRun

from app.matching.assignment.solver import (
    CandidateAssignmentView,
    solve_greedy_assignment,
)
from app.matching.candidate_generation.candidate_service import CandidateService
from app.matching.scoring.guardrails import evaluate_guardrails


@dataclass
class CandidateRuntimeRow:
    candidate_key: str
    payment_record_id: Any
    bank_transaction_id: Any
    block_reason: str
    features: Any
    score_result: Any
    guardrail_result: Any
    rank_for_payment: int | None = None
    rank_for_bank: int | None = None
    score_gap_to_next_payment_candidate: float | None = None
    score_gap_to_next_bank_candidate: float | None = None
    is_selected_match: bool = False
    assignment_status: str | None = None
    route_status: str | None = None


class ReconciliationRunService:
    def __init__(self, db: Session):
        self.db = db
        self.candidate_service = CandidateService()

    def run(
        self,
        *,
        triggered_by: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> ReconciliationRun:
        run = ReconciliationRun(
            status="running",
            triggered_by=triggered_by,
            parameters_json=parameters or {},
        )
        self.db.add(run)
        self.db.flush()

        payments = self._load_payment_records()
        banks = self._load_bank_transactions()

        built_candidates = self.candidate_service.build_candidates(payments, banks)
        runtime_rows = self._build_runtime_rows(built_candidates)

        self._apply_competition_context(runtime_rows)
        self._re_evaluate_guardrails_with_competition(runtime_rows)
        self._apply_assignment(runtime_rows)
        self._persist_candidates_and_features(run, runtime_rows)
        self._finalize_run_counts(run, runtime_rows)

        self.db.commit()
        self.db.refresh(run)
        return run

    def _load_payment_records(self) -> list[PaymentRecord]:
        return self.db.query(PaymentRecord).all()

    def _load_bank_transactions(self) -> list[BankTransaction]:
        return self.db.query(BankTransaction).all()

    def _build_runtime_rows(self, built_candidates) -> list[CandidateRuntimeRow]:
        runtime_rows: list[CandidateRuntimeRow] = []

        for idx, candidate in enumerate(built_candidates, start=1):
            runtime_rows.append(
                CandidateRuntimeRow(
                    candidate_key=f"cand_{idx}",
                    payment_record_id=candidate.payment_record_id,
                    bank_transaction_id=candidate.bank_transaction_id,
                    block_reason=candidate.block_reason,
                    features=candidate.features,
                    score_result=candidate.score_result,
                    guardrail_result=candidate.guardrail_result,
                )
            )

        return runtime_rows

    def _apply_competition_context(self, runtime_rows: list[CandidateRuntimeRow]) -> None:
        by_payment: dict[Any, list[CandidateRuntimeRow]] = defaultdict(list)
        by_bank: dict[Any, list[CandidateRuntimeRow]] = defaultdict(list)

        for row in runtime_rows:
            by_payment[row.payment_record_id].append(row)
            by_bank[row.bank_transaction_id].append(row)

        for rows in by_payment.values():
            rows.sort(key=lambda r: r.score_result.raw_score, reverse=True)
            for idx, row in enumerate(rows, start=1):
                row.rank_for_payment = idx
                row.score_gap_to_next_payment_candidate = self._score_gap_to_next(rows, idx - 1)

        for rows in by_bank.values():
            rows.sort(key=lambda r: r.score_result.raw_score, reverse=True)
            for idx, row in enumerate(rows, start=1):
                row.rank_for_bank = idx
                row.score_gap_to_next_bank_candidate = self._score_gap_to_next(rows, idx - 1)

    def _score_gap_to_next(
        self,
        ordered_rows: list[CandidateRuntimeRow],
        current_index: int,
    ) -> float | None:
        if current_index + 1 >= len(ordered_rows):
            return None

        current_score = ordered_rows[current_index].score_result.raw_score
        next_score = ordered_rows[current_index + 1].score_result.raw_score
        return round(current_score - next_score, 4)

    def _re_evaluate_guardrails_with_competition(
        self,
        runtime_rows: list[CandidateRuntimeRow],
    ) -> None:
        for row in runtime_rows:
            row.guardrail_result = evaluate_guardrails(
                features=row.features,
                score_result=row.score_result,
                second_best_gap_for_payment=row.score_gap_to_next_payment_candidate,
                second_best_gap_for_bank=row.score_gap_to_next_bank_candidate,
            )

    def _apply_assignment(self, runtime_rows: list[CandidateRuntimeRow]) -> None:
        assignment_views = [
            CandidateAssignmentView(
                candidate_id=row.candidate_key,
                payment_record_id=str(row.payment_record_id),
                bank_transaction_id=str(row.bank_transaction_id),
                raw_score=row.score_result.raw_score,
                auto_match_eligible=row.guardrail_result.auto_match_eligible,
            )
            for row in runtime_rows
        ]

        assignment_result = solve_greedy_assignment(assignment_views)
        selected_ids = set(assignment_result.selected_candidate_ids)

        for row in runtime_rows:
            row.is_selected_match = row.candidate_key in selected_ids
            row.assignment_status = "assigned" if row.is_selected_match else "not_assigned"

            if row.is_selected_match and row.guardrail_result.auto_match_eligible:
                row.route_status = "auto_match"
            elif row.is_selected_match:
                row.route_status = "review"
            else:
                row.route_status = "unmatched"

    def _persist_candidates_and_features(
        self,
        run: ReconciliationRun,
        runtime_rows: list[CandidateRuntimeRow],
    ) -> None:
        for row in runtime_rows:
            match_candidate = MatchCandidate(
                reconciliation_run_id=run.id,
                payment_record_id=row.payment_record_id,
                bank_transaction_id=row.bank_transaction_id,
                block_reason=row.block_reason,
                raw_score=row.score_result.raw_score,
                score_reasons_json=row.score_result.reasons,
                score_warnings_json=row.score_result.warnings,
                guardrail_flags_json=row.guardrail_result.flags,
                auto_match_eligible=row.guardrail_result.auto_match_eligible,
                assignment_status=row.assignment_status,
                route_status=row.route_status,
                is_selected_match=row.is_selected_match,
                rank_for_payment=row.rank_for_payment,
                rank_for_bank=row.rank_for_bank,
                score_gap_to_next_payment_candidate=row.score_gap_to_next_payment_candidate,
                score_gap_to_next_bank_candidate=row.score_gap_to_next_bank_candidate,
            )
            self.db.add(match_candidate)
            self.db.flush()

            candidate_feature = CandidateFeature(
                reconciliation_run_id=run.id,
                match_candidate_id=match_candidate.id,
                amount_diff_abs=self._to_float(row.features.amount_diff_abs),
                amount_match_exact=row.features.amount_match_exact,
                currency_match=row.features.currency_match,
                date_diff_days_signed=row.features.date_diff_days_signed,
                date_diff_days_abs=row.features.date_diff_days_abs,
                date_within_tolerance=row.features.date_within_tolerance,
                reference_exact_match=row.features.reference_exact_match,
                reference_substring_match=row.features.reference_substring_match,
                reference_similarity=row.features.reference_similarity,
                reference_missing_warning=row.features.reference_missing_warning,
                counterparty_exact_match=row.features.counterparty_exact_match,
                counterparty_similarity=row.features.counterparty_similarity,
                description_similarity=row.features.description_similarity,
                duplicate_amount_count_payment_side=row.features.duplicate_amount_count_payment_side,
                duplicate_amount_count_bank_side=row.features.duplicate_amount_count_bank_side,
                duplicate_amount_ambiguity=row.features.duplicate_amount_ambiguity,
                reversal_flag_bank=row.features.reversal_flag_bank,
            )
            self.db.add(candidate_feature)

    def _finalize_run_counts(
        self,
        run: ReconciliationRun,
        runtime_rows: list[CandidateRuntimeRow],
    ) -> None:
        run.candidate_count = len(runtime_rows)
        run.assigned_count = sum(1 for row in runtime_rows if row.assignment_status == "assigned")
        run.auto_matched_count = sum(1 for row in runtime_rows if row.route_status == "auto_match")
        run.review_count = sum(1 for row in runtime_rows if row.route_status == "review")
        run.unmatched_count = sum(1 for row in runtime_rows if row.route_status == "unmatched")
        run.status = "completed"

    @staticmethod
    def _to_float(value: Decimal | float | int) -> float:
        return float(value)