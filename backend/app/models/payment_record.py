from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    raw_import_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_import_files.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_row_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    payment_record_reference: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    invoice_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    customer_name_raw: Mapped[str] = mapped_column(Text, nullable=False)
    customer_name_normalized: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    expected_payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)

    reference_text_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_text_normalized: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


Index(
    "ix_payment_records_import_row_unique",
    PaymentRecord.raw_import_file_id,
    PaymentRecord.source_row_number,
    unique=True,
)