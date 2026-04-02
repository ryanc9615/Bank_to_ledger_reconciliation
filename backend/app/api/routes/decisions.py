from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.schemas.decisions import (
    AuditLogItemResponse,
    AuditLogListResponse,
    DecisionCreateRequest,
    DecisionListResponse,
    DecisionResponse,
)
from app.services.decisions.decision_service import DecisionService

router = APIRouter(tags=["decisions"])


@router.post("/decisions", response_model=DecisionResponse)
def create_decision(request: DecisionCreateRequest, db: Session = Depends(get_db)):
    service = DecisionService()
    decision = service.submit_decision(db, request)

    return DecisionResponse(
        decision_id=decision.id,
        run_id=decision.run_id,
        payment_record_id=decision.payment_record_id,
        bank_transaction_id=decision.bank_transaction_id,
        match_candidate_id=decision.match_candidate_id,
        decision_action=decision.decision_action,
        decision_status=decision.decision_status,
        reviewer_name=decision.reviewer_name,
        review_comment=decision.review_comment,
        decision_reason_code=decision.decision_reason_code,
        created_at=decision.created_at,
        is_active=decision.is_active,
    )


@router.get("/reconciliation/runs/{run_id}/decisions", response_model=DecisionListResponse)
def list_run_decisions(run_id: UUID, db: Session = Depends(get_db)):
    service = DecisionService()
    decisions = service.list_run_decisions(db, run_id)

    return DecisionListResponse(
        items=[
            DecisionResponse(
                decision_id=row.id,
                run_id=row.run_id,
                payment_record_id=row.payment_record_id,
                bank_transaction_id=row.bank_transaction_id,
                match_candidate_id=row.match_candidate_id,
                decision_action=row.decision_action,
                decision_status=row.decision_status,
                reviewer_name=row.reviewer_name,
                review_comment=row.review_comment,
                decision_reason_code=row.decision_reason_code,
                created_at=row.created_at,
                is_active=row.is_active,
            )
            for row in decisions
        ]
    )


@router.get("/reconciliation/runs/{run_id}/audit-log", response_model=AuditLogListResponse)
def list_run_audit_log(run_id: UUID, db: Session = Depends(get_db)):
    service = DecisionService()
    logs = service.list_run_audit_log(db, run_id)

    return AuditLogListResponse(
        items=[
            AuditLogItemResponse(
                id=row.id,
                decision_id=row.decision_id,
                run_id=row.run_id,
                payment_record_id=row.payment_record_id,
                bank_transaction_id=row.bank_transaction_id,
                match_candidate_id=row.match_candidate_id,
                event_type=row.event_type,
                actor_name=row.actor_name,
                before_state=row.before_state,
                after_state=row.after_state,
                request_payload=row.request_payload,
                evidence_snapshot=row.evidence_snapshot,
                notes=row.notes,
                event_timestamp=row.event_timestamp,
            )
            for row in logs
        ]
    )