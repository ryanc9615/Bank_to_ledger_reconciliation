from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.matching.common.accessors import (
    get_bank_amount,
    get_bank_booking_date,
    get_bank_counterparty_name_normalized,
    get_bank_currency,
    get_bank_description_normalized,
    get_bank_is_reversal,
    get_bank_reference_normalized,
    get_payment_amount,
    get_payment_currency,
    get_payment_customer_name_normalized,
    get_payment_expected_date,
    get_payment_reference_normalized,
)
from app.matching.features.similarity import (
    best_text_similarity,
    exact_text_match,
    substring_match,
)

AMOUNT_TOLERANCE = Decimal("0.01")
DATE_TOLERANCE_DAYS = 10


@dataclass
class CandidateFeatures:
    amount_diff_abs: Decimal
    amount_match_exact: bool
    currency_match: bool

    date_diff_days_signed: int | None
    date_diff_days_abs: int | None
    date_within_tolerance: bool

    reference_exact_match: bool
    reference_substring_match: bool
    reference_similarity: float
    reference_missing_warning: bool

    counterparty_exact_match: bool
    counterparty_similarity: float

    description_similarity: float

    duplicate_amount_count_payment_side: int
    duplicate_amount_count_bank_side: int
    duplicate_amount_ambiguity: bool

    reversal_flag_bank: bool


def safe_date_diff_days(left: date | None, right: date | None) -> tuple[int | None, int | None]:
    if left is None or right is None:
        return None, None

    signed = (right - left).days
    return signed, abs(signed)


def build_candidate_features(
    payment,
    bank,
    *,
    duplicate_amount_count_payment_side: int = 1,
    duplicate_amount_count_bank_side: int = 1,
) -> CandidateFeatures:
    payment_amount = Decimal(str(get_payment_amount(payment)))
    bank_amount = Decimal(str(get_bank_amount(bank)))

    amount_diff_abs = abs(payment_amount - bank_amount)
    amount_match_exact = amount_diff_abs <= AMOUNT_TOLERANCE
    currency_match = get_payment_currency(payment) == get_bank_currency(bank)

    date_signed, date_abs = safe_date_diff_days(
        get_payment_expected_date(payment),
        get_bank_booking_date(bank),
    )
    date_within_tolerance = date_abs is not None and date_abs <= DATE_TOLERANCE_DAYS

    payment_ref = get_payment_reference_normalized(payment)
    bank_ref = get_bank_reference_normalized(bank)

    reference_exact = exact_text_match(payment_ref, bank_ref)
    reference_substring = substring_match(payment_ref, bank_ref)
    reference_similarity = best_text_similarity(payment_ref, bank_ref)
    reference_missing_warning = not bool((bank_ref or "").strip())

    payment_name = get_payment_customer_name_normalized(payment)
    bank_name = get_bank_counterparty_name_normalized(bank)

    counterparty_exact = exact_text_match(payment_name, bank_name)
    counterparty_similarity = best_text_similarity(payment_name, bank_name)

    description_similarity = best_text_similarity(
        payment_ref,
        get_bank_description_normalized(bank),
    )

    duplicate_amount_ambiguity = (
        duplicate_amount_count_payment_side > 1
        or duplicate_amount_count_bank_side > 1
    )

    reversal_flag_bank = get_bank_is_reversal(bank)

    return CandidateFeatures(
        amount_diff_abs=amount_diff_abs,
        amount_match_exact=amount_match_exact,
        currency_match=currency_match,
        date_diff_days_signed=date_signed,
        date_diff_days_abs=date_abs,
        date_within_tolerance=date_within_tolerance,
        reference_exact_match=reference_exact,
        reference_substring_match=reference_substring,
        reference_similarity=reference_similarity,
        reference_missing_warning=reference_missing_warning,
        counterparty_exact_match=counterparty_exact,
        counterparty_similarity=counterparty_similarity,
        description_similarity=description_similarity,
        duplicate_amount_count_payment_side=duplicate_amount_count_payment_side,
        duplicate_amount_count_bank_side=duplicate_amount_count_bank_side,
        duplicate_amount_ambiguity=duplicate_amount_ambiguity,
        reversal_flag_bank=reversal_flag_bank,
    )