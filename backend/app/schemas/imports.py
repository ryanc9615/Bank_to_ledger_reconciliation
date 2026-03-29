from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ImportType = Literal["bank_transactions", "payment_records"]


class ValidationErrorItem(BaseModel):
    row_number: int
    field_name: str
    error_code: str
    message: str
    raw_value: str | int | float | list[str] | None = None


class ImportSummary(BaseModel):
    raw_import_file_id: UUID
    import_type: ImportType
    source_filename: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[ValidationErrorItem] = Field(default_factory=list)
    created_record_ids: list[UUID] = Field(default_factory=list)
    uploaded_at: datetime
    created_count: int = 0
    duplicate_count: int = 0