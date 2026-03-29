from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    raw_import_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_import_files.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    external_row_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # credit | debit

    reference_text_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_text_normalized: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    counterparty_text_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    counterparty_text_normalized: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    transaction_description_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_description_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)

    bank_transaction_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_reversal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


Index(
    "ix_bank_transactions_import_row_unique",
    BankTransaction.raw_import_file_id,
    BankTransaction.source_row_number,
    unique=True,
)