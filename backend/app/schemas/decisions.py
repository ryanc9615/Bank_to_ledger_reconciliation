from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


DecisionAction = Literal[
    "accept",
    "reject",
    "write_off",
    "investigate_later",
    "mark_duplicate",
    "manual_match_override",
]

DecisionStatus = Literal[
    "resolved_matched",
    "resolved_unmatched",
    "resolved_write_off",
    "resolved_duplicate",
    "deferred",
]


class DecisionCreateRequest(BaseModel):
    run_id: UUID
    payment_record_id: UUID
    bank_transaction_id: Optional[UUID] = None
    match_candidate_id: Optional[UUID] = None
    decision_action: DecisionAction
    reviewer_name: str = Field(min_length=1, max_length=255)
    review_comment: Optional[str] = None
    decision_reason_code: Optional[str] = None
    manual_override_bank_transaction_id: Optional[UUID] = None


class DecisionResponse(BaseModel):
    decision_id: UUID
    run_id: UUID
    payment_record_id: UUID
    bank_transaction_id: Optional[UUID] = None
    match_candidate_id: Optional[UUID] = None
    decision_action: DecisionAction
    decision_status: DecisionStatus
    reviewer_name: str
    review_comment: Optional[str] = None
    decision_reason_code: Optional[str] = None
    created_at: datetime
    is_active: bool


class DecisionListResponse(BaseModel):
    items: list[DecisionResponse]


class AuditLogItemResponse(BaseModel):
    id: UUID
    decision_id: Optional[UUID] = None
    run_id: UUID
    payment_record_id: UUID
    bank_transaction_id: Optional[UUID] = None
    match_candidate_id: Optional[UUID] = None
    event_type: str
    actor_name: str
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    request_payload: Optional[dict[str, Any]] = None
    evidence_snapshot: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    event_timestamp: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItemResponse]