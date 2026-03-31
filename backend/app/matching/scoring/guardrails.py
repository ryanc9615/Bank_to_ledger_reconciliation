from __future__ import annotations

from dataclasses import dataclass

from app.matching.features.feature_builder import CandidateFeatures
from app.matching.scoring.rule_score import ScoreResult

AUTO_MATCH_THRESHOLD = 0.95
NEAR_TIE_MARGIN = 0.03
TIGHT_DATE_DAYS = 3


@dataclass
class GuardrailResult:
    auto_match_eligible: bool
    flags: list[str]


def has_strong_reference_evidence(features: CandidateFeatures) -> bool:
    """
    Reference-led evidence path for auto-match eligibility.
    """
    return (
        features.reference_exact_match
        or features.reference_substring_match
        or features.reference_similarity >= 0.90
    )


def has_strong_counterparty_evidence(features: CandidateFeatures) -> bool:
    """
    Counterparty-led evidence path for cases where reference is weak/missing.
    """
    return (
        features.counterparty_exact_match
        or features.counterparty_similarity >= 0.90
    )


def has_tight_date_evidence(features: CandidateFeatures) -> bool:
    """
    Tight timing support used when reference evidence is not dominant.
    """
    return (
        features.date_diff_days_abs is not None
        and features.date_diff_days_abs <= TIGHT_DATE_DAYS
    )


def evaluate_guardrails(
    *,
    features: CandidateFeatures,
    score_result: ScoreResult,
    second_best_gap_for_payment: float | None = None,
    second_best_gap_for_bank: float | None = None,
) -> GuardrailResult:
    """
    Evaluate whether a candidate is safe enough for automatic matching.

    Important:
    - high score alone is not sufficient
    - flags are explicit so downstream workflow can explain why
      a candidate was blocked from auto-match
    """
    flags: list[str] = []

    if score_result.raw_score < AUTO_MATCH_THRESHOLD:
        flags.append("below auto-match threshold")

    if not features.amount_match_exact:
        flags.append("amount mismatch")

    if not features.currency_match:
        flags.append("currency mismatch")

    if not features.date_within_tolerance:
        flags.append("date outside tolerance")

    if features.reversal_flag_bank:
        flags.append("reversal/refund anomaly")

    if features.duplicate_amount_ambiguity:
        flags.append("duplicate amount ambiguity")

    strong_reference = has_strong_reference_evidence(features)
    strong_counterparty = has_strong_counterparty_evidence(features)
    tight_date = has_tight_date_evidence(features)

    if not (strong_reference or (strong_counterparty and tight_date)):
        flags.append("insufficient strong evidence shape")

    if (
        second_best_gap_for_payment is not None
        and second_best_gap_for_payment < NEAR_TIE_MARGIN
    ):
        flags.append("near-tie warning")

    if (
        second_best_gap_for_bank is not None
        and second_best_gap_for_bank < NEAR_TIE_MARGIN
    ):
        flags.append("near-tie warning")

    auto_match_eligible = len(flags) == 0

    return GuardrailResult(
        auto_match_eligible=auto_match_eligible,
        flags=flags,
    )