from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.matching.candidate_generation.blocking import should_generate_candidate


@dataclass
class DummyPaymentRecord:
    id: str
    amount: Decimal
    currency_code: str
    expected_payment_date: date | None
    reference_normalized: str | None
    customer_name_normalized: str | None


@dataclass
class DummyBankTransaction:
    id: str
    amount: Decimal
    currency_code: str
    booking_date: date | None
    reference_normalized: str | None
    counterparty_name_normalized: str | None
    direction: str
    is_reversal: bool = False


def test_blocking_accepts_amount_date_window():
    payment = DummyPaymentRecord(
        id="p1",
        amount=Decimal("1250.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 10),
        reference_normalized="INV100245",
        customer_name_normalized="ALPHALTD",
    )
    bank = DummyBankTransaction(
        id="b1",
        amount=Decimal("1250.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 12),
        reference_normalized="PAYINV100245",
        counterparty_name_normalized="ALPHALTD",
        direction="credit",
        is_reversal=False,
    )

    include, reason = should_generate_candidate(payment, bank)

    assert include is True
    assert reason == "amount_date_window"


def test_blocking_accepts_reference_hint_when_date_window_misses():
    payment = DummyPaymentRecord(
        id="p1",
        amount=Decimal("399.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 1),
        reference_normalized="INV100777",
        customer_name_normalized="BETAGROUP",
    )
    bank = DummyBankTransaction(
        id="b1",
        amount=Decimal("399.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 25),
        reference_normalized="PAYINV100777",
        counterparty_name_normalized="OTHERNAME",
        direction="credit",
        is_reversal=False,
    )

    include, reason = should_generate_candidate(payment, bank)

    assert include is True
    assert reason == "amount_reference_hint"


def test_blocking_rejects_non_credit():
    payment = DummyPaymentRecord(
        id="p1",
        amount=Decimal("250.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 20),
        reference_normalized="INV100111",
        customer_name_normalized="OMEGALTD",
    )
    bank = DummyBankTransaction(
        id="b1",
        amount=Decimal("250.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 20),
        reference_normalized="INV100111",
        counterparty_name_normalized="OMEGALTD",
        direction="debit",
        is_reversal=False,
    )

    include, reason = should_generate_candidate(payment, bank)

    assert include is False
    assert reason is None


def test_blocking_rejects_reversal():
    payment = DummyPaymentRecord(
        id="p1",
        amount=Decimal("100.00"),
        currency_code="GBP",
        expected_payment_date=date(2026, 3, 10),
        reference_normalized="INV100001",
        customer_name_normalized="ALPHALTD",
    )
    bank = DummyBankTransaction(
        id="b1",
        amount=Decimal("100.00"),
        currency_code="GBP",
        booking_date=date(2026, 3, 10),
        reference_normalized="INV100001",
        counterparty_name_normalized="ALPHALTD",
        direction="credit",
        is_reversal=True,
    )

    include, reason = should_generate_candidate(payment, bank)

    assert include is False
    assert reason is None