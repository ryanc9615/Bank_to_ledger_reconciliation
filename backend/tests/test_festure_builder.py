from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.matching.features.feature_builder import (
    build_candidate_features,
    safe_date_diff_days,
)


@dataclass
class DummyPaymentRecord:
    amount: Decimal
    currency_code: str
    expected_payment_date: date | None
    reference_normalized: str | None
    customer_name_normalized: str | None


@dataclass
class DummyBankTransaction:
    amount: Decimal
    currency_code: str
    booking_date: date | None
    reference_normalized: str | None
    counterparty_name_normalized: str | None
    description_normalized: str | None
    is_reversal: bool = False


def test_safe_date_diff_days_returns_signed_and_abs():
    signed, abs_days = safe_date_diff_days(date(2026, 3, 10), date(2026, 3, 12))
    assert signed == 2
    assert abs_days == 2


def test_build_candidate_features_strong_match_case():
    payment = DummyPaymentRecord(
        amount=Decimal("1250.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 10),
        reference_normalized="INV100245",
        customer_name_normalized="ALPHALTD",
    )

    bank = DummyBankTransaction(
        amount=Decimal("1250.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 11),
        reference_normalized="PAYINV100245",
        counterparty_name_normalized="ALPHALTD",
        description_normalized="PAYMENTINV100245",
        is_reversal=False,
    )

    features = build_candidate_features(
        payment,
        bank,
        duplicate_amount_count_payment_side=1,
        duplicate_amount_count_bank_side=1,
    )

    assert features.amount_match_exact is True
    assert features.currency_match is True
    assert features.date_within_tolerance is True
    assert features.reference_substring_match is True
    assert features.reference_similarity > 0.0
    assert features.counterparty_exact_match is True
    assert features.reference_missing_warning is False
    assert features.duplicate_amount_ambiguity is False
    assert features.reversal_flag_bank is False


def test_build_candidate_features_missing_reference_warning():
    payment = DummyPaymentRecord(
        amount=Decimal("399.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 15),
        reference_normalized="INV100777",
        customer_name_normalized="BETAGROUP",
    )

    bank = DummyBankTransaction(
        amount=Decimal("399.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 18),
        reference_normalized=None,
        counterparty_name_normalized="BETAGROUP",
        description_normalized="CUSTOMERPAYMENT",
        is_reversal=False,
    )

    features = build_candidate_features(payment, bank)

    assert features.amount_match_exact is True
    assert features.reference_missing_warning is True
    assert features.counterparty_similarity > 0.0


def test_build_candidate_features_duplicate_amount_ambiguity():
    payment = DummyPaymentRecord(
        amount=Decimal("250.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 20),
        reference_normalized="INV100111",
        customer_name_normalized="OMEGALTD",
    )

    bank = DummyBankTransaction(
        amount=Decimal("250.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 20),
        reference_normalized="INV100111",
        counterparty_name_normalized="OMEGALTD",
        description_normalized="INV100111",
        is_reversal=False,
    )

    features = build_candidate_features(
        payment,
        bank,
        duplicate_amount_count_payment_side=2,
        duplicate_amount_count_bank_side=1,
    )

    assert features.duplicate_amount_ambiguity is True


def test_build_candidate_features_reversal_flag():
    payment = DummyPaymentRecord(
        amount=Decimal("100.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 10),
        reference_normalized="INV100001",
        customer_name_normalized="ALPHALTD",
    )

    bank = DummyBankTransaction(
        amount=Decimal("100.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 10),
        reference_normalized="INV100001",
        counterparty_name_normalized="ALPHALTD",
        description_normalized="REVERSALINV100001",
        is_reversal=True,
    )

    features = build_candidate_features(payment, bank)

    assert features.reversal_flag_bank is True