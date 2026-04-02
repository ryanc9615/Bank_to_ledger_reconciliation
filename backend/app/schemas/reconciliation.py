from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


QueueType = Literal[
    "auto_matched",
    "review",
    "unmatched_payments",
    "unmatched_bank",
    "deferred",
]


class ReconciliationRunStartRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReconciliationRunSummary(BaseModel):
    candidate_count: int
    assigned_count: int
    auto_matched_count: int
    review_count: int
    unmatched_payment_count: int
    unmatched_bank_count: int


class ReconciliationRunResponse(BaseModel):
    run_id: UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: dict[str, Any]
    summary: ReconciliationRunSummary


class ReconciliationRunListItem(BaseModel):
    run_id: UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_count: int
    auto_matched_count: int
    review_count: int


class ReconciliationRunListResponse(BaseModel):
    items: list[ReconciliationRunListItem]


class RecordSummary(BaseModel):
    id: UUID
    external_row_id: Optional[str] = None
    amount: float
    currency_code: str
    reference_text: Optional[str] = None
    customer_name: Optional[str] = None
    counterparty_text: Optional[str] = None
    transaction_description: Optional[str] = None
    expected_payment_date: Optional[date] = None
    booking_date: Optional[date] = None


class ProposalSummaryResponse(BaseModel):
    candidate_id: UUID
    run_id: UUID
    payment_record_id: UUID
    bank_transaction_id: UUID
    selected: bool
    route_status: str
    score: float
    rank_for_payment: Optional[int] = None
    rank_for_bank: Optional[int] = None
    score_reasons: list[str]
    score_warnings: list[str]


class ProposalListResponse(BaseModel):
    items: list[ProposalSummaryResponse]


class CandidateFeaturesResponse(BaseModel):
    amount_diff: Optional[float] = None
    amount_exact_match: Optional[bool] = None
    currency_match: Optional[bool] = None
    date_diff_days: Optional[int] = None
    date_within_tolerance: Optional[bool] = None
    reference_exact_match: Optional[bool] = None
    reference_substring_match: Optional[bool] = None
    reference_similarity: Optional[float] = None
    counterparty_similarity: Optional[float] = None
    description_similarity: Optional[float] = None
    duplicate_amount_ambiguity: Optional[bool] = None
    is_reversal: Optional[bool] = None


class ProposalAlternateResponse(BaseModel):
    candidate_id: UUID
    score: float
    rank_for_payment: Optional[int] = None
    selected: bool


class ProposalDetailResponse(BaseModel):
    candidate_id: UUID
    run_id: UUID
    payment_record: RecordSummary
    bank_transaction: RecordSummary
    score: float
    selected: bool
    route_status: str
    score_reasons: list[str]
    score_warnings: list[str]
    guardrail_flags: list[str]
    features: CandidateFeaturesResponse
    alternatives: list[ProposalAlternateResponse]
    current_decision: Optional[dict[str, Any]] = None


class QueueItemResponse(BaseModel):
    workflow_item_type: str
    payment_record_id: Optional[UUID] = None
    bank_transaction_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    score: Optional[float] = None
    score_reasons: list[str] = Field(default_factory=list)
    score_warnings: list[str] = Field(default_factory=list)
    payment_summary: Optional[RecordSummary] = None
    bank_summary: Optional[RecordSummary] = None
    current_decision: Optional[dict[str, Any]] = None
    available_actions: list[str] = Field(default_factory=list)


class QueueResponse(BaseModel):
    run_id: UUID
    queue_type: QueueType
    count: int
    items: list[QueueItemResponse]