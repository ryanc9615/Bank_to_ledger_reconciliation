from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.matching.common.accessors import (
    get_bank_amount,
    get_bank_booking_date,
    get_bank_counterparty_name_normalized,
    get_bank_currency,
    get_bank_direction,
    get_bank_is_reversal,
    get_bank_reference_normalized,
    get_payment_amount,
    get_payment_currency,
    get_payment_customer_name_normalized,
    get_payment_expected_date,
    get_payment_reference_normalized,
)

AMOUNT_TOLERANCE = Decimal("0.01")
DATE_WINDOW_DAYS_BACK = 5
DATE_WINDOW_DAYS_FORWARD = 10


def amount_matches(a, b, tolerance: Decimal = AMOUNT_TOLERANCE) -> bool:
    return abs(Decimal(str(a)) - Decimal(str(b))) <= tolerance


def within_date_window(
    expected_date,
    booking_date,
    *,
    days_back: int = DATE_WINDOW_DAYS_BACK,
    days_forward: int = DATE_WINDOW_DAYS_FORWARD,
) -> bool:
    if expected_date is None or booking_date is None:
        return False

    earliest = expected_date - timedelta(days=days_back)
    latest = expected_date + timedelta(days=days_forward)
    return earliest <= booking_date <= latest


def has_reference_hint(payment, bank) -> bool:
    payment_ref = (get_payment_reference_normalized(payment) or "").strip()
    bank_ref = (get_bank_reference_normalized(bank) or "").strip()

    if not payment_ref or not bank_ref:
        return False

    return payment_ref in bank_ref or bank_ref in payment_ref


def has_counterparty_hint(payment, bank) -> bool:
    payment_name = (get_payment_customer_name_normalized(payment) or "").strip()
    bank_name = (get_bank_counterparty_name_normalized(bank) or "").strip()

    if not payment_name or not bank_name:
        return False

    return payment_name == bank_name


def should_generate_candidate(payment, bank) -> tuple[bool, str | None]:
    if get_payment_currency(payment) != get_bank_currency(bank):
        return False, None

    if get_bank_direction(bank) != "credit":
        return False, None

    if get_bank_is_reversal(bank):
        return False, None

    if not amount_matches(get_payment_amount(payment), get_bank_amount(bank)):
        return False, None

    if within_date_window(get_payment_expected_date(payment), get_bank_booking_date(bank)):
        return True, "amount_date_window"

    if has_reference_hint(payment, bank):
        return True, "amount_reference_hint"

    if has_counterparty_hint(payment, bank):
        return True, "amount_counterparty_hint"

    return False, None