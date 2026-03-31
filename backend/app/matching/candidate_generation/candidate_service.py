from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.matching.common.accessors import (
    get_bank_amount,
    get_bank_id,
    get_payment_amount,
    get_payment_id,
)
from app.matching.candidate_generation.blocking import should_generate_candidate
from app.matching.features.feature_builder import CandidateFeatures, build_candidate_features
from app.matching.scoring.guardrails import GuardrailResult, evaluate_guardrails
from app.matching.scoring.rule_score import ScoreResult, score_candidate


@dataclass
class CandidateBuildResult:
    payment_record_id: object
    bank_transaction_id: object
    block_reason: str

    features: CandidateFeatures
    score_result: ScoreResult
    guardrail_result: GuardrailResult


class CandidateService:
    def build_candidates(self, payments, bank_transactions) -> list[CandidateBuildResult]:
        payment_amount_counts = Counter(str(get_payment_amount(payment)) for payment in payments)
        bank_amount_counts = Counter(str(get_bank_amount(bank)) for bank in bank_transactions)

        built_candidates: list[CandidateBuildResult] = []

        for payment in payments:
            for bank in bank_transactions:
                include, block_reason = should_generate_candidate(payment, bank)
                if not include or block_reason is None:
                    continue

                features = build_candidate_features(
                    payment,
                    bank,
                    duplicate_amount_count_payment_side=payment_amount_counts[str(get_payment_amount(payment))],
                    duplicate_amount_count_bank_side=bank_amount_counts[str(get_bank_amount(bank))],
                )

                score_result = score_candidate(features)
                guardrail_result = evaluate_guardrails(
                    features=features,
                    score_result=score_result,
                )

                built_candidates.append(
                    CandidateBuildResult(
                        payment_record_id=get_payment_id(payment),
                        bank_transaction_id=get_bank_id(bank),
                        block_reason=block_reason,
                        features=features,
                        score_result=score_result,
                        guardrail_result=guardrail_result,
                    )
                )

        return built_candidates