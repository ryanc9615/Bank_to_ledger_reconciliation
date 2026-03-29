from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.imports import ImportSummary
from app.services.imports.import_service import ImportService


router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/bank-transactions", response_model=ImportSummary)
async def import_bank_transactions(
    file: UploadFile = File(...),
    source_system: str | None = Form(default="manual_upload"),
    db: Session = Depends(get_db),
) -> ImportSummary:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_bytes = await file.read()

    service = ImportService(db)
    return service.import_csv(
        import_type="bank_transactions",
        filename=file.filename,
        content_type=file.content_type,
        file_bytes=file_bytes,
        source_system=source_system,
    )


@router.post("/payment-records", response_model=ImportSummary)
async def import_payment_records(
    file: UploadFile = File(...),
    source_system: str | None = Form(default="manual_upload"),
    db: Session = Depends(get_db),
) -> ImportSummary:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_bytes = await file.read()

    service = ImportService(db)
    return service.import_csv(
        import_type="payment_records",
        filename=file.filename,
        content_type=file.content_type,
        file_bytes=file_bytes,
        source_system=source_system,
    )