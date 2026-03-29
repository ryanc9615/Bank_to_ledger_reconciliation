from __future__ import annotations

import hashlib
from collections import Counter
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.bank_transaction import BankTransaction
from app.models.payment_record import PaymentRecord
from app.models.raw_import_file import RawImportFile
from app.schemas.imports import ImportSummary, ValidationErrorItem
from app.services.imports.column_mapping import map_to_canonical
from app.services.imports.parser import (
    FileParsingError,
    parse_csv_bytes,
    validate_required_headers,
)
from app.services.normalization.normalization_service import (
    RowValidationError,
    normalize_bank_transaction_row,
    normalize_payment_record_row,
)

ImportType = Literal["bank_transactions", "payment_records"]


REQUIRED_HEADERS: dict[ImportType, set[str]] = {
    "bank_transactions": {
        "transaction_date",
        "booking_date",
        "amount",
        "currency_code",
        "direction",
        "reference_text",
        "counterparty_text",
        "transaction_description",
    },
    "payment_records": {
        "payment_record_reference",
        "customer_name",
        "expected_payment_date",
        "amount",
        "currency_code",
        "reference_text",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def import_csv(
        self,
        *,
        import_type: ImportType,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
        source_system: str | None = None,
    ) -> ImportSummary:
        checksum = sha256_bytes(file_bytes)

        raw_import = RawImportFile(
            import_type=import_type,
            source_filename=filename,
            source_content_type=content_type,
            source_system=source_system,
            file_size_bytes=len(file_bytes),
            file_checksum_sha256=checksum,
            status="uploaded",
        )
        self.db.add(raw_import)
        self.db.flush()

        try:
            parsed = parse_csv_bytes(file_bytes)
        except FileParsingError as exc:
            raw_import.status = "failed_validation"
            raw_import.error_summary_json = {"file_errors": [str(exc)]}
            self.db.commit()
            self.db.refresh(raw_import)

            return ImportSummary(
                raw_import_file_id=raw_import.id,
                import_type=import_type,
                source_filename=filename,
                status=raw_import.status,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=[
                    ValidationErrorItem(
                        row_number=0,
                        field_name="file",
                        error_code="file_parse_error",
                        message=str(exc),
                        raw_value=None,
                    )
                ],
                created_record_ids=[],
                uploaded_at=raw_import.uploaded_at,
                created_count=0,
                duplicate_count=0,
            )

        raw_import.raw_headers_json = parsed.headers
        raw_import.total_rows = parsed.total_rows

        mapped = map_to_canonical(import_type, parsed.headers, parsed.rows)
        raw_import.notes = f"detected_source={mapped.detected_source}"

        missing_headers = validate_required_headers(
            mapped.canonical_headers,
            REQUIRED_HEADERS[import_type],
        )

        if missing_headers:
            raw_import.status = "failed_validation"
            raw_import.invalid_rows = parsed.total_rows
            raw_import.error_summary_json = {"missing_headers": missing_headers}
            self.db.commit()
            self.db.refresh(raw_import)

            return ImportSummary(
                raw_import_file_id=raw_import.id,
                import_type=import_type,
                source_filename=filename,
                status=raw_import.status,
                total_rows=parsed.total_rows,
                valid_rows=0,
                invalid_rows=parsed.total_rows,
                errors=[
                    ValidationErrorItem(
                        row_number=0,
                        field_name="headers",
                        error_code="missing_required_headers",
                        message=f"Missing required headers: {', '.join(missing_headers)}",
                        raw_value=missing_headers,
                    )
                ],
                created_record_ids=[],
                uploaded_at=raw_import.uploaded_at,
                created_count=0,
                duplicate_count=0,
            )

        created_record_ids: list[UUID] = []
        row_errors: list[ValidationErrorItem] = []
        duplicate_count = 0

        if import_type == "bank_transactions":
            existing_external_ids = {
                value
                for (value,) in self.db.query(BankTransaction.external_row_id).all()
                if value is not None
            }
        else:
            existing_external_ids = {
                value
                for (value,) in self.db.query(PaymentRecord.external_row_id).all()
                if value is not None
            }

        for idx, row in enumerate(mapped.canonical_rows, start=2):
            try:
                if import_type == "bank_transactions":
                    canonical = normalize_bank_transaction_row(row)

                    if canonical.external_row_id in existing_external_ids:
                        duplicate_count += 1
                        continue

                    entity = BankTransaction(
                        raw_import_file_id=raw_import.id,
                        source_row_number=idx,
                        external_row_id=canonical.external_row_id,
                        account_number=canonical.account_number,
                        sort_code=canonical.sort_code,
                        bank_account_name=canonical.bank_account_name,
                        transaction_date=canonical.transaction_date,
                        booking_date=canonical.booking_date,
                        value_date=canonical.value_date,
                        amount=canonical.amount,
                        currency_code=canonical.currency_code,
                        direction=canonical.direction,
                        reference_text_raw=canonical.reference_text_raw,
                        reference_text_normalized=canonical.reference_text_normalized,
                        counterparty_text_raw=canonical.counterparty_text_raw,
                        counterparty_text_normalized=canonical.counterparty_text_normalized,
                        transaction_description_raw=canonical.transaction_description_raw,
                        transaction_description_normalized=canonical.transaction_description_normalized,
                        bank_transaction_type=canonical.bank_transaction_type,
                        is_reversal=canonical.is_reversal,
                    )

                else:
                    canonical = normalize_payment_record_row(row)

                    if canonical.external_row_id in existing_external_ids:
                        duplicate_count += 1
                        continue

                    entity = PaymentRecord(
                        raw_import_file_id=raw_import.id,
                        source_row_number=idx,
                        external_row_id=canonical.external_row_id,
                        payment_record_reference=canonical.payment_record_reference,
                        invoice_reference=canonical.invoice_reference,
                        customer_id=canonical.customer_id,
                        customer_name_raw=canonical.customer_name_raw,
                        customer_name_normalized=canonical.customer_name_normalized,
                        expected_payment_date=canonical.expected_payment_date,
                        due_date=canonical.due_date,
                        amount=canonical.amount,
                        currency_code=canonical.currency_code,
                        reference_text_raw=canonical.reference_text_raw,
                        reference_text_normalized=canonical.reference_text_normalized,
                        status=canonical.status,
                    )

                self.db.add(entity)
                self.db.flush()
                created_record_ids.append(entity.id)
                existing_external_ids.add(canonical.external_row_id)

            except RowValidationError as exc:
                row_errors.append(
                    ValidationErrorItem(
                        row_number=idx,
                        field_name=exc.field_name,
                        error_code=exc.error_code,
                        message=exc.message,
                        raw_value=exc.raw_value,
                    )
                )

        created_count = len(created_record_ids)
        invalid_count = len(row_errors)
        valid_count = created_count + duplicate_count

        raw_import.valid_rows = valid_count
        raw_import.invalid_rows = invalid_count
        raw_import.status = "imported" if invalid_count == 0 else "parsed_with_errors"

        error_counter = Counter(error.error_code for error in row_errors)
        raw_import.error_summary_json = {
            "error_counts": dict(error_counter),
            "created_count": created_count,
            "duplicate_count": duplicate_count,
        }

        self.db.commit()
        self.db.refresh(raw_import)

        return ImportSummary(
            raw_import_file_id=raw_import.id,
            import_type=import_type,
            source_filename=filename,
            status=raw_import.status,
            total_rows=parsed.total_rows,
            valid_rows=raw_import.valid_rows,
            invalid_rows=raw_import.invalid_rows,
            errors=row_errors,
            created_record_ids=created_record_ids,
            uploaded_at=raw_import.uploaded_at,
            created_count=created_count,
            duplicate_count=duplicate_count,
        )