from app.matching.features.similarity import (
    best_text_similarity,
    exact_text_match,
    normalize_none,
    sequence_similarity,
    substring_match,
    token_jaccard_similarity,
)


def test_normalize_none_handles_none():
    assert normalize_none(None) == ""


def test_normalize_none_strips_whitespace():
    assert normalize_none("  INV100001  ") == "INV100001"


def test_exact_text_match_true_for_identical_non_empty_strings():
    assert exact_text_match("INV100001", "INV100001") is True


def test_exact_text_match_false_for_empty_strings():
    assert exact_text_match("", "") is False
    assert exact_text_match(None, None) is False


def test_substring_match_detects_embedded_reference():
    assert substring_match("INV100245", "PAYINV100245") is True


def test_substring_match_false_when_no_overlap():
    assert substring_match("INV100245", "INV100999") is False


def test_sequence_similarity_is_high_for_close_strings():
    score = sequence_similarity("ALPHALTD", "ALPHAGROUPLTD")
    assert 0.5 <= score <= 1.0


def test_token_jaccard_similarity_works_for_name_overlap():
    score = token_jaccard_similarity("ALPHA LTD", "ALPHA GROUP LTD")
    assert score > 0.0


def test_best_text_similarity_returns_bounded_score():
    score = best_text_similarity("INV100245", "PAYINV100245")
    assert 0.0 <= score <= 1.0