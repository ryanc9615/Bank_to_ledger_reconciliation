from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class DashboardMetricsResponse(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    latest_run_id: UUID | None = None
    latest_run_auto_matched_count: int = 0
    latest_run_review_count: int = 0
    latest_run_unmatched_payment_count: int = 0
    latest_run_unmatched_bank_count: int = 0


class RunMetricsResponse(BaseModel):
    run_id: UUID
    assigned_count: int
    auto_matched_count: int
    review_count: int
    unmatched_payment_count: int
    unmatched_bank_count: int
    decision_count: int
    deferred_count: int
    resolved_count: int


class QueueMetricsResponse(BaseModel):
    run_id: UUID
    auto_matched_count: int
    review_count: int
    unmatched_payment_count: int
    unmatched_bank_count: int
    deferred_count: int