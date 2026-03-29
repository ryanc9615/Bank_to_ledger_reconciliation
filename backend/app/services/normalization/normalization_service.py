from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.services.normalization.text_normalizer import (
    normalize_free_text,
    normalize_name_text,
    normalize_reference_text,
)


class RowValidationError(Exception):
    def __init__(self, field_name: str, error_code: str, message: str, raw_value: object | None = None):
        self.field_name = field_name
        self.error_code = error_code
        self.message = message
        self.raw_value = raw_value
        super().__init__(message)


@dataclass
class CanonicalBankTransactionRow:
    external_row_id: str | None
    account_number: str | None
    sort_code: str | None
    bank_account_name: str | None
    transaction_date: date
    booking_date: date
    value_date: date | None
    amount: Decimal
    currency_code: str
    direction: str
    reference_text_raw: str | None
    reference_text_normalized: str | None
    counterparty_text_raw: str | None
    counterparty_text_normalized: str | None
    transaction_description_raw: str | None
    transaction_description_normalized: str | None
    bank_transaction_type: str | None
    is_reversal: bool


@dataclass
class CanonicalPaymentRecordRow:
    external_row_id: str | None
    payment_record_reference: str
    invoice_reference: str | None
    customer_id: str | None
    customer_name_raw: str
    customer_name_normalized: str
    expected_payment_date: date
    due_date: date | None
    amount: Decimal
    currency_code: str
    reference_text_raw: str | None
    reference_text_normalized: str | None
    status: str | None


SUPPORTED_CURRENCIES = {"GBP", "USD", "EUR"}


def parse_date(value: str | None, field_name: str) -> date:
    if value is None or not value.strip():
        raise RowValidationError(field_name, "required", f"{field_name} is required.", value)

    raw = value.strip()

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    raise RowValidationError(field_name, "invalid_date", f"Invalid date format for {field_name}.", value)


def parse_optional_date(value: str | None, field_name: str) -> date | None:
    if value is None or not value.strip():
        return None
    return parse_date(value, field_name)


def parse_currency(value: str | None, field_name: str = "currency_code") -> str:
    if value is None or not value.strip():
        raise RowValidationError(field_name, "required", "Currency code is required.", value)

    raw = value.strip().upper()

    symbol_map = {
        "£": "GBP",
        "$": "USD",
        "€": "EUR",
    }
    raw = symbol_map.get(raw, raw)

    if raw not in SUPPORTED_CURRENCIES:
        raise RowValidationError(field_name, "invalid_currency", f"Unsupported currency code: {raw}", value)

    return raw


def parse_amount(value: str | None, field_name: str = "amount") -> Decimal:
    if value is None or not value.strip():
        raise RowValidationError(field_name, "required", "Amount is required.", value)

    raw = value.strip().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    if raw.startswith("(") and raw.endswith(")"):
        raw = f"-{raw[1:-1]}"

    try:
        amount = Decimal(raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise RowValidationError(field_name, "invalid_amount", "Amount must be numeric.", value) from exc

    if amount == Decimal("0.00"):
        raise RowValidationError(field_name, "invalid_amount", "Amount cannot be zero.", value)

    return amount


def derive_signed_amount(amount: Decimal, direction: str, field_name: str = "direction") -> Decimal:
    direction_lower = direction.strip().lower()
    if direction_lower not in {"credit", "debit"}:
        raise RowValidationError(field_name, "invalid_direction", "Direction must be 'credit' or 'debit'.", direction)

    if direction_lower == "credit":
        return abs(amount)
    return -abs(amount)


def normalize_bank_transaction_row(row: dict[str, str]) -> CanonicalBankTransactionRow:
    raw_direction = (row.get("direction") or "").strip().lower()
    parsed_amount = parse_amount(row.get("amount"), "amount")
    signed_amount = derive_signed_amount(parsed_amount, raw_direction, "direction")

    reference_raw = row.get("reference_text")
    counterparty_raw = row.get("counterparty_text")
    description_raw = row.get("transaction_description")

    return CanonicalBankTransactionRow(
        external_row_id=(row.get("external_row_id") or None),
        account_number=(row.get("account_number") or None),
        sort_code=(row.get("sort_code") or None),
        bank_account_name=(row.get("bank_account_name") or None),
        transaction_date=parse_date(row.get("transaction_date"), "transaction_date"),
        booking_date=parse_date(row.get("booking_date"), "booking_date"),
        value_date=parse_optional_date(row.get("value_date"), "value_date"),
        amount=signed_amount,
        currency_code=parse_currency(row.get("currency_code")),
        direction=raw_direction,
        reference_text_raw=reference_raw or None,
        reference_text_normalized=normalize_reference_text(reference_raw),
        counterparty_text_raw=counterparty_raw or None,
        counterparty_text_normalized=normalize_name_text(counterparty_raw),
        transaction_description_raw=description_raw or None,
        transaction_description_normalized=normalize_free_text(description_raw),
        bank_transaction_type=(row.get("bank_transaction_type") or None),
        is_reversal=((row.get("is_reversal") or "").strip().lower() in {"true", "1", "yes"}),
    )


def normalize_payment_record_row(row: dict[str, str]) -> CanonicalPaymentRecordRow:
    customer_name_raw = row.get("customer_name")
    if customer_name_raw is None or not customer_name_raw.strip():
        raise RowValidationError("customer_name", "required", "customer_name is required.", customer_name_raw)

    payment_record_reference = row.get("payment_record_reference")
    if payment_record_reference is None or not payment_record_reference.strip():
        raise RowValidationError(
            "payment_record_reference",
            "required",
            "payment_record_reference is required.",
            payment_record_reference,
        )

    amount = parse_amount(row.get("amount"), "amount")
    if amount < 0:
        raise RowValidationError("amount", "invalid_amount", "payment_records amount must be positive.", str(amount))

    reference_raw = row.get("reference_text")

    return CanonicalPaymentRecordRow(
        external_row_id=(row.get("external_row_id") or None),
        payment_record_reference=payment_record_reference.strip(),
        invoice_reference=(row.get("invoice_reference") or None),
        customer_id=(row.get("customer_id") or None),
        customer_name_raw=customer_name_raw.strip(),
        customer_name_normalized=normalize_name_text(customer_name_raw) or customer_name_raw.strip().upper(),
        expected_payment_date=parse_date(row.get("expected_payment_date"), "expected_payment_date"),
        due_date=parse_optional_date(row.get("due_date"), "due_date"),
        amount=amount,
        currency_code=parse_currency(row.get("currency_code")),
        reference_text_raw=reference_raw or None,
        reference_text_normalized=normalize_reference_text(reference_raw),
        status=(row.get("status") or None),
    )