from __future__ import annotations

import random


def apply_reference_noise(
    expected_reference: str,
    rng: random.Random,
    missing_rate: float,
    truncated_rate: float,
    max_length: int,
) -> tuple[str, str]:
    """
    Returns:
        noisy_reference, noise_type
    """
    x = rng.random()

    if x < missing_rate:
        return "", "missing_reference"

    if x < missing_rate + truncated_rate:
        truncated = _truncate_reference(expected_reference, rng, max_length)
        return truncated, "truncated_reference"

    clean = expected_reference[:max_length]
    return clean, "clean_reference"


def _truncate_reference(reference: str, rng: random.Random, max_length: int) -> str:
    reference = reference[:max_length]

    strategies = [
        lambda s: s[: max(4, len(s) // 2)],
        lambda s: s[-min(6, len(s)):],
        lambda s: "".join(ch for ch in s if ch.isdigit())[:max_length] or s[:6],
        lambda s: s.replace("INV-", "")[:max_length],
    ]
    return rng.choice(strategies)(reference)