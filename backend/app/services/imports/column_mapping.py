from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ImportType = Literal["bank_transactions", "payment_records"]


@dataclass(frozen=True)
class SourceMappingResult:
    canonical_headers: list[str]
    canonical_rows: list[dict[str, str]]
    detected_source: str


PACK_B_BANK_MAPPING: dict[str, str] = {
    "bank_transaction_id": "external_row_id",
    "booking_date": "booking_date",
    "value_date": "value_date",
    "amount": "amount",
    "currency": "currency_code",
    "transaction_type": "direction",
    "payer_name": "counterparty_text",
    "payer_reference": "reference_text",
    "bank_description": "transaction_description",
    "is_reversal": "is_reversal",
}

PACK_B_PAYMENT_MAPPING: dict[str, str] = {
    "payment_record_id": "external_row_id",
    "customer_id": "customer_id",
    "customer_name": "customer_name",
    "expected_amount": "amount",
    "currency": "currency_code",
    "due_date": "due_date",
    "expected_payment_date": "expected_payment_date",
    "expected_reference": "reference_text",
}

PACK_B_PAYMENT_DERIVED_MAPPING: dict[str, str] = {
    "payment_record_id": "payment_record_reference",
    "invoice_number": "invoice_reference",
}


def remap_row(row: dict[str, str], mapping: dict[str, str]) -> dict[str, str]:
    canonical_row: dict[str, str] = {}

    for source_key, canonical_key in mapping.items():
        if source_key in row:
            canonical_row[canonical_key] = row[source_key]

    return canonical_row


def detect_pack_b_bank(headers: list[str]) -> bool:
    required = {
        "bank_transaction_id",
        "booking_date",
        "amount",
        "currency",
        "transaction_type",
        "payer_name",
        "payer_reference",
        "bank_description",
    }
    return required.issubset(set(headers))


def detect_pack_b_payment(headers: list[str]) -> bool:
    required = {
        "payment_record_id",
        "customer_name",
        "expected_amount",
        "currency",
        "expected_payment_date",
        "expected_reference",
    }
    return required.issubset(set(headers))


def map_to_canonical(import_type: ImportType, headers: list[str], rows: list[dict[str, str]]) -> SourceMappingResult:
    header_set = set(headers)

    # Case 1: already canonical enough, pass through unchanged
    if import_type == "bank_transactions":
        canonical_required_subset = {
            "booking_date",
            "amount",
            "currency_code",
            "direction",
            "reference_text",
            "counterparty_text",
            "transaction_description",
        }
        if canonical_required_subset.issubset(header_set):
            return SourceMappingResult(
                canonical_headers=headers,
                canonical_rows=rows,
                detected_source="canonical_bank",
            )

        if detect_pack_b_bank(headers):
            canonical_rows: list[dict[str, str]] = []
            for row in rows:
                canonical_row = remap_row(row, PACK_B_BANK_MAPPING)

                # Pack B does not have a separate transaction_date field.
                # For V1 we map booking_date -> transaction_date explicitly.
                canonical_row["transaction_date"] = row.get("booking_date", "")

                # Map transaction_type values to canonical direction values.
                raw_txn_type = (row.get("transaction_type") or "").strip().lower()
                if raw_txn_type in {"credit", "unexpected_credit"}:
                    canonical_row["direction"] = "credit"
                elif raw_txn_type == "reversal":
                    canonical_row["direction"] = "debit"
                else:
                    canonical_row["direction"] = raw_txn_type

                canonical_rows.append(canonical_row)

            canonical_headers = sorted({key for row in canonical_rows for key in row.keys()})
            return SourceMappingResult(
                canonical_headers=canonical_headers,
                canonical_rows=canonical_rows,
                detected_source="pack_b_bank",
            )

    if import_type == "payment_records":
        canonical_required_subset = {
            "payment_record_reference",
            "customer_name",
            "expected_payment_date",
            "amount",
            "currency_code",
            "reference_text",
        }
        if canonical_required_subset.issubset(header_set):
            return SourceMappingResult(
                canonical_headers=headers,
                canonical_rows=rows,
                detected_source="canonical_payment",
            )

        if detect_pack_b_payment(headers):
            canonical_rows = []
            for row in rows:
                canonical_row = remap_row(row, PACK_B_PAYMENT_MAPPING)

                for source_key, canonical_key in PACK_B_PAYMENT_DERIVED_MAPPING.items():
                    canonical_row[canonical_key] = row.get(source_key, "")

                canonical_rows.append(canonical_row)

            canonical_headers = sorted({key for row in canonical_rows for key in row.keys()})
            return SourceMappingResult(
                canonical_headers=canonical_headers,
                canonical_rows=canonical_rows,
                detected_source="pack_b_payment",
            )

    # Fallback: return unchanged so downstream required-header validation still works cleanly
    return SourceMappingResult(
        canonical_headers=headers,
        canonical_rows=rows,
        detected_source="unknown",
    )