from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import uuid


@dataclass
class CandidateAssignmentView:
    candidate_id: str
    payment_record_id: uuid.UUID
    bank_transaction_id: uuid.UUID
    raw_score: float
    auto_match_eligible: bool = False


@dataclass
class AssignmentResult:
    selected_candidate_ids: list[str]
    rejected_candidate_ids: list[str]


def solve_greedy_assignment(
    candidates: Iterable[CandidateAssignmentView],
    minimum_score: float = 0.50,
) -> AssignmentResult:
    """
    Select a one-to-one set of matches using a simple greedy strategy:
    highest score first, skipping conflicts.

    V1 design intent:
    - transparent
    - deterministic
    - easy to test
    - easy to replace later with a more global optimizer
    """
    eligible_candidates = [
        candidate
        for candidate in candidates
        if candidate.raw_score >= minimum_score
    ]

    ordered = sorted(
        eligible_candidates,
        key=lambda candidate: candidate.raw_score,
        reverse=True,
    )

    matched_payments: set[str] = set()
    matched_banks: set[str] = set()

    selected_candidate_ids: list[str] = []
    rejected_candidate_ids: list[str] = []

    for candidate in ordered:
        payment_already_matched = candidate.payment_record_id in matched_payments
        bank_already_matched = candidate.bank_transaction_id in matched_banks

        if payment_already_matched or bank_already_matched:
            rejected_candidate_ids.append(candidate.candidate_id)
            continue

        selected_candidate_ids.append(candidate.candidate_id)
        matched_payments.add(candidate.payment_record_id)
        matched_banks.add(candidate.bank_transaction_id)

    return AssignmentResult(
        selected_candidate_ids=selected_candidate_ids,
        rejected_candidate_ids=rejected_candidate_ids,
    )