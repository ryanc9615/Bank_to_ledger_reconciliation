from decimal import Decimal

from app.matching.features.feature_builder import CandidateFeatures
from app.matching.scoring.rule_score import score_candidate


def make_features(**overrides) -> CandidateFeatures:
    base = CandidateFeatures(
        amount_diff_abs=Decimal("0.00"),
        amount_match_exact=True,
        currency_match=True,
        date_diff_days_signed=1,
        date_diff_days_abs=1,
        date_within_tolerance=True,
        reference_exact_match=False,
        reference_substring_match=True,
        reference_similarity=0.8571,
        reference_missing_warning=False,
        counterparty_exact_match=True,
        counterparty_similarity=1.0,
        description_similarity=0.72,
        duplicate_amount_count_payment_side=1,
        duplicate_amount_count_bank_side=1,
        duplicate_amount_ambiguity=False,
        reversal_flag_bank=False,
    )
    return CandidateFeatures(**{**base.__dict__, **overrides})


def test_score_candidate_strong_case():
    features = make_features()

    result = score_candidate(features)

    assert result.raw_score == 0.92
    assert "exact amount match" in result.reasons
    assert "booked date within tolerance" in result.reasons
    assert "high reference similarity" in result.reasons
    assert "counterparty similarity" in result.reasons
    assert result.warnings == []


def test_score_candidate_exact_reference_can_reach_max():
    features = make_features(
        date_diff_days_signed=0,
        date_diff_days_abs=0,
        reference_exact_match=True,
        reference_substring_match=False,
        reference_similarity=1.0,
    )

    result = score_candidate(features)

    assert result.raw_score == 1.0
    assert "exact reference match" in result.reasons


def test_score_candidate_missing_reference_adds_warning():
    features = make_features(
        reference_exact_match=False,
        reference_substring_match=False,
        reference_similarity=0.0,
        reference_missing_warning=True,
    )

    result = score_candidate(features)

    assert "missing reference warning" in result.warnings
    assert result.subscores["reference"] == 0.0


def test_score_candidate_duplicate_amount_adds_warning():
    features = make_features(duplicate_amount_ambiguity=True)

    result = score_candidate(features)

    assert "duplicate amount ambiguity" in result.warnings


def test_score_candidate_reversal_adds_warning():
    features = make_features(reversal_flag_bank=True)

    result = score_candidate(features)

    assert "reversal/refund anomaly" in result.warnings


def test_score_candidate_no_exact_amount_collapses_score():
    features = make_features(
        amount_match_exact=False,
        amount_diff_abs=Decimal("10.00"),
    )

    result = score_candidate(features)

    assert result.subscores["amount"] == 0.0
    assert result.raw_score < 0.92


def test_score_candidate_score_bounded_to_one():
    features = make_features(
        date_diff_days_signed=0,
        date_diff_days_abs=0,
        reference_exact_match=True,
        reference_substring_match=False,
        reference_similarity=1.0,
        counterparty_exact_match=True,
        counterparty_similarity=1.0,
    )

    result = score_candidate(features)

    assert 0.0 <= result.raw_score <= 1.0