from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.matching.candidate_generation.candidate_service import CandidateService


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
    description_normalized: str | None
    direction: str
    is_reversal: bool = False


def test_candidate_service_builds_candidates():
    payments = [
        DummyPaymentRecord(
            id="p1",
            amount=Decimal("1250.00"),
            currency_code="GBP",
            expected_payment_date=date(2026, 3, 10),
            reference_normalized="INV100245",
            customer_name_normalized="ALPHALTD",
        )
    ]

    bank_transactions = [
        DummyBankTransaction(
            id="b1",
            amount=Decimal("1250.00"),
            currency_code="GBP",
            booking_date=date(2026, 3, 11),
            reference_normalized="PAYINV100245",
            counterparty_name_normalized="ALPHALTD",
            description_normalized="PAYMENTINV100245",
            direction="credit",
            is_reversal=False,
        ),
        DummyBankTransaction(
            id="b2",
            amount=Decimal("999.00"),
            currency_code="GBP",
            booking_date=date(2026, 3, 11),
            reference_normalized="OTHER",
            counterparty_name_normalized="OTHER",
            description_normalized="OTHER",
            direction="credit",
            is_reversal=False,
        ),
    ]

    service = CandidateService()
    results = service.build_candidates(payments, bank_transactions)

    assert len(results) == 1

    candidate = results[0]
    assert candidate.payment_record_id == "p1"
    assert candidate.bank_transaction_id == "b1"
    assert candidate.block_reason == "amount_date_window"
    assert candidate.score_result.raw_score > 0.0


def test_candidate_service_sets_duplicate_amount_ambiguity():
    payments = [
        DummyPaymentRecord(
            id="p1",
            amount=Decimal("250.00"),
            currency_code="GBP",
            expected_payment_date=date(2026, 3, 20),
            reference_normalized="INV100111",
            customer_name_normalized="OMEGALTD",
        ),
        DummyPaymentRecord(
            id="p2",
            amount=Decimal("250.00"),
            currency_code="GBP",
            expected_payment_date=date(2026, 3, 21),
            reference_normalized="INV100112",
            customer_name_normalized="OMEGALTD",
        ),
    ]

    bank_transactions = [
        DummyBankTransaction(
            id="b1",
            amount=Decimal("250.00"),
            currency_code="GBP",
            booking_date=date(2026, 3, 20),
            reference_normalized="INV100111",
            counterparty_name_normalized="OMEGALTD",
            description_normalized="INV100111",
            direction="credit",
            is_reversal=False,
        )
    ]

    service = CandidateService()
    results = service.build_candidates(payments, bank_transactions)

    assert len(results) >= 1
    assert any(r.features.duplicate_amount_ambiguity for r in results)