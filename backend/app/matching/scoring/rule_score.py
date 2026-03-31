from __future__ import annotations

from dataclasses import dataclass

from app.matching.features.feature_builder import CandidateFeatures


@dataclass
class ScoreResult:
    raw_score: float
    reasons: list[str]
    warnings: list[str]
    subscores: dict[str, float]


def score_amount_component(features: CandidateFeatures) -> float:
    """
    V1 assumes exact amount is foundational for one-to-one AR-style matching.
    """
    if features.amount_match_exact and features.currency_match:
        return 0.45
    return 0.0


def score_date_component(features: CandidateFeatures) -> float:
    """
    Date evidence decays as the booking date moves further away
    from expected payment date.
    """
    days = features.date_diff_days_abs

    if days is None:
        return 0.0
    if days == 0:
        return 0.20
    if days <= 3:
        return 0.16
    if days <= 7:
        return 0.12
    if days <= 10:
        return 0.08
    return 0.0


def score_reference_component(features: CandidateFeatures) -> float:
    """
    Reference evidence hierarchy:
    exact > substring > high similarity > moderate similarity
    """
    if features.reference_exact_match:
        return 0.20
    if features.reference_substring_match:
        return 0.16
    if features.reference_similarity >= 0.90:
        return 0.14
    if features.reference_similarity >= 0.80:
        return 0.10
    if features.reference_similarity >= 0.70:
        return 0.05
    return 0.0


def score_counterparty_component(features: CandidateFeatures) -> float:
    """
    Counterparty/customer evidence is supportive rather than primary.
    """
    if features.counterparty_exact_match:
        return 0.15
    if features.counterparty_similarity >= 0.90:
        return 0.12
    if features.counterparty_similarity >= 0.80:
        return 0.08
    if features.counterparty_similarity >= 0.70:
        return 0.04
    return 0.0


def score_candidate(features: CandidateFeatures) -> ScoreResult:
    """
    Produce a deterministic, explainable score from feature evidence.
    """

    reasons: list[str] = []
    warnings: list[str] = []
    subscores: dict[str, float] = {}

    amount_score = score_amount_component(features)
    subscores["amount"] = amount_score
    if amount_score > 0:
        reasons.append("exact amount match")

    date_score = score_date_component(features)
    subscores["date"] = date_score
    if date_score > 0:
        reasons.append("booked date within tolerance")

    reference_score = score_reference_component(features)
    subscores["reference"] = reference_score
    if features.reference_exact_match:
        reasons.append("exact reference match")
    elif features.reference_substring_match or features.reference_similarity >= 0.70:
        reasons.append("high reference similarity")

    counterparty_score = score_counterparty_component(features)
    subscores["counterparty"] = counterparty_score
    if counterparty_score > 0:
        reasons.append("counterparty similarity")

    if features.reference_missing_warning:
        warnings.append("missing reference warning")

    if features.duplicate_amount_ambiguity:
        warnings.append("duplicate amount ambiguity")

    if features.reversal_flag_bank:
        warnings.append("reversal/refund anomaly")

    raw_score = round(
        amount_score + date_score + reference_score + counterparty_score,
        4,
    )

    raw_score = min(raw_score, 1.0)

    return ScoreResult(
        raw_score=raw_score,
        reasons=reasons,
        warnings=warnings,
        subscores=subscores,
    )