from decimal import Decimal

from app.matching.features.feature_builder import CandidateFeatures
from app.matching.scoring.guardrails import evaluate_guardrails
from app.matching.scoring.rule_score import ScoreResult


def make_features(**overrides) -> CandidateFeatures:
    base = CandidateFeatures(
        amount_diff_abs=Decimal("0.00"),
        amount_match_exact=True,
        currency_match=True,
        date_diff_days_signed=0,
        date_diff_days_abs=0,
        date_within_tolerance=True,
        reference_exact_match=True,
        reference_substring_match=False,
        reference_similarity=1.0,
        reference_missing_warning=False,
        counterparty_exact_match=True,
        counterparty_similarity=1.0,
        description_similarity=1.0,
        duplicate_amount_count_payment_side=1,
        duplicate_amount_count_bank_side=1,
        duplicate_amount_ambiguity=False,
        reversal_flag_bank=False,
    )
    return CandidateFeatures(**{**base.__dict__, **overrides})


def make_score(raw_score: float) -> ScoreResult:
    return ScoreResult(
        raw_score=raw_score,
        reasons=[],
        warnings=[],
        subscores={},
    )


def test_guardrails_pass_for_elite_clean_candidate():
    features = make_features()
    score_result = make_score(1.0)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
        second_best_gap_for_payment=0.10,
        second_best_gap_for_bank=0.10,
    )

    assert result.auto_match_eligible is True
    assert result.flags == []


def test_guardrails_fail_below_threshold():
    features = make_features()
    score_result = make_score(0.92)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
    )

    assert result.auto_match_eligible is False
    assert "below auto-match threshold" in result.flags


def test_guardrails_fail_duplicate_amount_ambiguity():
    features = make_features(duplicate_amount_ambiguity=True)
    score_result = make_score(0.98)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
    )

    assert result.auto_match_eligible is False
    assert "duplicate amount ambiguity" in result.flags


def test_guardrails_fail_reversal_flag():
    features = make_features(reversal_flag_bank=True)
    score_result = make_score(0.98)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
    )

    assert result.auto_match_eligible is False
    assert "reversal/refund anomaly" in result.flags


def test_guardrails_fail_near_tie_on_payment_side():
    features = make_features()
    score_result = make_score(0.98)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
        second_best_gap_for_payment=0.01,
        second_best_gap_for_bank=0.10,
    )

    assert result.auto_match_eligible is False
    assert "near-tie warning" in result.flags


def test_guardrails_fail_insufficient_evidence_shape():
    features = make_features(
        reference_exact_match=False,
        reference_substring_match=False,
        reference_similarity=0.20,
        counterparty_exact_match=False,
        counterparty_similarity=0.60,
        date_diff_days_signed=7,
        date_diff_days_abs=7,
    )
    score_result = make_score(0.97)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
        second_best_gap_for_payment=0.10,
        second_best_gap_for_bank=0.10,
    )

    assert result.auto_match_eligible is False
    assert "insufficient strong evidence shape" in result.flags


def test_guardrails_allow_counterparty_plus_tight_date_path():
    features = make_features(
        reference_exact_match=False,
        reference_substring_match=False,
        reference_similarity=0.0,
        counterparty_exact_match=True,
        counterparty_similarity=1.0,
        date_diff_days_signed=2,
        date_diff_days_abs=2,
    )
    score_result = make_score(0.97)

    result = evaluate_guardrails(
        features=features,
        score_result=score_result,
        second_best_gap_for_payment=0.10,
        second_best_gap_for_bank=0.10,
    )

    assert result.auto_match_eligible is True