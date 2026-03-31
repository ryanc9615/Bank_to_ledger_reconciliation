from __future__ import annotations

from difflib import SequenceMatcher
from typing import Set


def normalize_none(value: str | None) -> str:
    """
    Convert None to empty string and strip surrounding whitespace.

    This keeps downstream comparison helpers simple and null-safe.
    """
    return (value or "").strip()


def exact_text_match(a: str | None, b: str | None) -> bool:
    """
    Return True only when both normalized strings are non-empty and identical.

    This is the strongest text evidence in the V1 matching engine.
    """
    a_norm = normalize_none(a)
    b_norm = normalize_none(b)

    return bool(a_norm) and a_norm == b_norm


def substring_match(a: str | None, b: str | None, min_len: int = 6) -> bool:
    """
    Return True when one normalized string is contained inside the other.

    Intended for truncated or embedded references such as:
    - INV100245 vs PAYINV100245

    min_len protects against weak matches on very short strings.
    """
    a_norm = normalize_none(a)
    b_norm = normalize_none(b)

    if not a_norm or not b_norm:
        return False

    if len(a_norm) < min_len and len(b_norm) < min_len:
        return False

    return a_norm in b_norm or b_norm in a_norm


def sequence_similarity(a: str | None, b: str | None) -> float:
    """
    Character-level similarity using Python's built-in SequenceMatcher.

    Returns a score between 0.0 and 1.0.
    """
    a_norm = normalize_none(a)
    b_norm = normalize_none(b)

    if not a_norm or not b_norm:
        return 0.0

    return round(SequenceMatcher(None, a_norm, b_norm).ratio(), 4)


def token_set(value: str | None) -> Set[str]:
    """
    Split normalized text into a distinct token set.

    This is mainly useful for counterparty / description comparisons.
    """
    text = normalize_none(value)
    if not text:
        return set()

    return {token for token in text.split() if token}


def token_jaccard_similarity(a: str | None, b: str | None) -> float:
    """
    Token-overlap similarity:
        |intersection| / |union|

    Returns a score between 0.0 and 1.0.
    """
    a_tokens = token_set(a)
    b_tokens = token_set(b)

    if not a_tokens or not b_tokens:
        return 0.0

    intersection = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)

    if union == 0:
        return 0.0

    return round(intersection / union, 4)


def best_text_similarity(a: str | None, b: str | None) -> float:
    """
    Return the stronger of:
    - sequence similarity
    - token Jaccard similarity

    This gives a simple V1 hybrid similarity without introducing
    heavier fuzzy-matching dependencies yet.
    """
    return max(
        sequence_similarity(a, b),
        token_jaccard_similarity(a, b),
    )