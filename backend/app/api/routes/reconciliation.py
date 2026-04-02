from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reconciliation import (
    ProposalDetailResponse,
    ProposalListResponse,
    ProposalSummaryResponse,
    QueueResponse,
    ReconciliationRunListItem,
    ReconciliationRunListResponse,
    ReconciliationRunResponse,
    ReconciliationRunStartRequest,
    ReconciliationRunSummary,
)
from app.services.reconciliation.query_service import (
    ProposalNotFoundError,
    QueueTypeError,
    ReconciliationQueryService,
    RunNotFoundError,
)
from app.services.reconciliation.run_service import ReconciliationRunService

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/runs", response_model=ReconciliationRunResponse)
def start_reconciliation_run(
    request: ReconciliationRunStartRequest,
    db: Session = Depends(get_db),
) -> ReconciliationRunResponse:
    """
    Start a new reconciliation run using the Pack D matching engine.
    """
    service = ReconciliationRunService(db)
    run = service.run(parameters=request.parameters)

    return ReconciliationRunResponse(
        run_id=run.id,
        status=run.status,
        started_at=getattr(run, "started_at", None),
        completed_at=getattr(run, "completed_at", None),
        parameters=getattr(run, "parameters_json", {}) or {},
        summary=ReconciliationRunSummary(
            candidate_count=getattr(run, "candidate_count", 0),
            assigned_count=getattr(run, "assigned_count", 0),
            auto_matched_count=getattr(run, "auto_matched_count", 0),
            review_count=getattr(run, "review_count", 0),
            unmatched_payment_count=getattr(run, "unmatched_count", 0),
            unmatched_bank_count=0,
        ),
    )


@router.get("/runs", response_model=ReconciliationRunListResponse)
def list_runs(db: Session = Depends(get_db)) -> ReconciliationRunListResponse:
    """
    List reconciliation runs in reverse chronological order.
    """
    query_service = ReconciliationQueryService()
    runs = query_service.list_runs(db)

    return ReconciliationRunListResponse(
        items=[
            ReconciliationRunListItem(
                run_id=run.id,
                status=run.status,
                started_at=run.started_at,
                completed_at=run.completed_at,
                assigned_count=run.assigned_count,
                auto_matched_count=run.auto_matched_count,
                review_count=run.review_count,
            )
            for run in runs
        ]
    )


@router.get("/runs/{run_id}", response_model=ReconciliationRunResponse)
def get_run(run_id: UUID, db: Session = Depends(get_db)) -> ReconciliationRunResponse:
    """
    Get one reconciliation run summary.
    """
    query_service = ReconciliationQueryService()

    try:
        run = query_service.get_run(db, run_id)
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ReconciliationRunResponse(
        run_id=run.id,
        status=run.status,
        started_at=getattr(run, "started_at", None),
        completed_at=getattr(run, "completed_at", None),
        parameters=getattr(run, "parameters_json", {}) or {},
        summary=ReconciliationRunSummary(
            candidate_count=getattr(run, "candidate_count", 0),
            assigned_count=getattr(run, "assigned_count", 0),
            auto_matched_count=getattr(run, "auto_matched_count", 0),
            review_count=getattr(run, "review_count", 0),
            unmatched_payment_count=getattr(run, "unmatched_count", 0),
            unmatched_bank_count=0,
        ),
    )


@router.get("/runs/{run_id}/summary", response_model=ReconciliationRunResponse)
def get_run_summary(run_id: UUID, db: Session = Depends(get_db)) -> ReconciliationRunResponse:
    """
    Alias endpoint for a run summary. Useful for frontend clarity.
    """
    query_service = ReconciliationQueryService()

    try:
        run = query_service.get_run(db, run_id)
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ReconciliationRunResponse(
        run_id=run.id,
        status=run.status,
        started_at=getattr(run, "started_at", None),
        completed_at=getattr(run, "completed_at", None),
        parameters=getattr(run, "parameters_json", {}) or {},
        summary=ReconciliationRunSummary(
            candidate_count=getattr(run, "candidate_count", 0),
            assigned_count=getattr(run, "assigned_count", 0),
            auto_matched_count=getattr(run, "auto_matched_count", 0),
            review_count=getattr(run, "review_count", 0),
            unmatched_payment_count=getattr(run, "unmatched_count", 0),
            unmatched_bank_count=0,
        ),
    )


@router.get("/runs/{run_id}/proposals", response_model=ProposalListResponse)
def list_run_proposals(
    run_id: UUID,
    selected_only: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> ProposalListResponse:
    """
    List proposal rows for a run.
    By default, returns selected proposals only because that is the main workflow-facing view.
    """
    query_service = ReconciliationQueryService()

    try:
        proposals = query_service.list_run_proposals(
            db,
            run_id,
            selected_only=selected_only,
        )
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ProposalListResponse(
        items=[
            ProposalSummaryResponse(
                candidate_id=row.id,
                run_id=row.reconciliation_run_id,
                payment_record_id=row.payment_record_id,
                bank_transaction_id=row.bank_transaction_id,
                selected=row.is_selected_match,
                route_status=row.route_status,
                score=row.raw_score,
                rank_for_payment=row.rank_for_payment,
                rank_for_bank=row.rank_for_bank,
                score_reasons=row.score_reasons_json or [],
                score_warnings=row.score_warnings_json or [],
            )
            for row in proposals
        ]
    )


@router.get("/runs/{run_id}/proposals/{candidate_id}", response_model=ProposalDetailResponse)
def get_proposal_detail(
    run_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
) -> ProposalDetailResponse:
    """
    Get detailed evidence for a single proposal in a specific run.
    Returns 404 if the candidate does not belong to that run.
    """
    query_service = ReconciliationQueryService()

    try:
        candidate, payment, bank, feature, alternatives, current_decision = (
            query_service.get_proposal_detail(db, run_id, candidate_id)
        )
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ProposalDetailResponse(
        candidate_id=candidate.id,
        run_id=candidate.reconciliation_run_id,
        payment_record={
            "id": payment.id,
            "external_row_id": getattr(payment, "external_row_id", None),
            "amount": payment.amount,
            "currency_code": payment.currency_code,
            "reference_text": getattr(payment, "reference_text_normalized", None),
            "customer_name": getattr(payment, "customer_name_normalized", None),
            "expected_payment_date": payment.expected_payment_date,
        },
        bank_transaction={
            "id": bank.id,
            "external_row_id": getattr(bank, "external_row_id", None),
            "amount": bank.amount,
            "currency_code": bank.currency_code,
            "reference_text": getattr(bank, "reference_text_normalized", None),
            "counterparty_text": getattr(bank, "counterparty_text_normalized", None),
            "transaction_description": getattr(bank, "transaction_description_normalized", None),
            "booking_date": bank.booking_date,
        },
        score=candidate.raw_score,
        selected=candidate.is_selected_match,
        route_status=candidate.route_status,
        score_reasons=candidate.score_reasons_json or [],
        score_warnings=candidate.score_warnings_json or [],
        guardrail_flags=candidate.guardrail_flags_json or {},
        features={
            "amount_diff": getattr(feature, "amount_diff", None) if feature else None,
            "amount_exact_match": getattr(feature, "amount_exact_match", None) if feature else None,
            "currency_match": getattr(feature, "currency_match", None) if feature else None,
            "date_diff_days": getattr(feature, "date_diff_days", None) if feature else None,
            "date_within_tolerance": getattr(feature, "date_within_tolerance", None) if feature else None,
            "reference_exact_match": getattr(feature, "reference_exact_match", None) if feature else None,
            "reference_substring_match": getattr(feature, "reference_substring_match", None) if feature else None,
            "reference_similarity": getattr(feature, "reference_similarity", None) if feature else None,
            "counterparty_similarity": getattr(feature, "counterparty_similarity", None) if feature else None,
            "description_similarity": getattr(feature, "description_similarity", None) if feature else None,
            "duplicate_amount_ambiguity": getattr(feature, "duplicate_amount_ambiguity", None) if feature else None,
            "is_reversal": getattr(feature, "is_reversal", None) if feature else None,
        },
        alternatives=[
            {
                "candidate_id": alt.id,
                "score": alt.raw_score,
                "rank_for_payment": alt.rank_for_payment,
                "selected": alt.is_selected_match,
            }
            for alt in alternatives
        ],
        current_decision=(
            {
                "decision_id": current_decision.id,
                "decision_action": current_decision.decision_action,
                "decision_status": current_decision.decision_status,
                "reviewer_name": current_decision.reviewer_name,
            }
            if current_decision
            else None
        ),
    )


@router.get("/runs/{run_id}/queues/{queue_type}", response_model=QueueResponse)
def get_queue_view(
    run_id: UUID,
    queue_type: str,
    db: Session = Depends(get_db),
) -> QueueResponse:
    """
    Return workflow-facing queue views derived from Pack D outputs and active decisions.
    Supported queue types:
      - auto_matched
      - review
      - unmatched_payments
      - unmatched_bank
      - deferred
    """
    query_service = ReconciliationQueryService()

    try:
        items = query_service.get_queue_items(db, run_id, queue_type)
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except QueueTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    shaped_items = []

    for item in items:
        if queue_type in {"auto_matched", "review"}:
            shaped_items.append(
                {
                    "workflow_item_type": (
                        "selected_candidate_review"
                        if queue_type == "review"
                        else "auto_matched_candidate"
                    ),
                    "payment_record_id": item.payment_record_id,
                    "bank_transaction_id": item.bank_transaction_id,
                    "candidate_id": item.id,
                    "score": item.raw_score,
                    "score_reasons": item.score_reasons_json or [],
                    "score_warnings": item.score_warnings_json or [],
                    "available_actions": (
                        [
                            "accept",
                            "reject",
                            "write_off",
                            "investigate_later",
                            "mark_duplicate",
                            "manual_match_override",
                        ]
                        if queue_type == "review"
                        else []
                    ),
                }
            )

        elif queue_type == "unmatched_payments":
            shaped_items.append(
                {
                    "workflow_item_type": "unmatched_payment",
                    "payment_record_id": item.id,
                    "payment_summary": {
                        "id": item.id,
                        "external_row_id": getattr(item, "external_row_id", None),
                        "amount": item.amount,
                        "currency_code": item.currency_code,
                        "reference_text": getattr(item, "reference_text_normalized", None),
                        "customer_name": getattr(item, "customer_name_normalized", None),
                        "expected_payment_date": item.expected_payment_date,
                    },
                    "available_actions": [
                        "write_off",
                        "investigate_later",
                        "manual_match_override",
                    ],
                }
            )

        elif queue_type == "unmatched_bank":
            shaped_items.append(
                {
                    "workflow_item_type": "unmatched_bank",
                    "bank_transaction_id": item.id,
                    "bank_summary": {
                        "id": item.id,
                        "external_row_id": getattr(item, "external_row_id", None),
                        "amount": item.amount,
                        "currency_code": item.currency_code,
                        "reference_text": getattr(item, "reference_text_normalized", None),
                        "counterparty_text": getattr(item, "counterparty_text_normalized", None),
                        "transaction_description": getattr(item, "transaction_description_normalized", None),
                        "booking_date": item.booking_date,
                    },
                    "available_actions": [
                        "mark_duplicate",
                        "investigate_later",
                        "manual_match_override",
                    ],
                }
            )

        elif queue_type == "deferred":
            shaped_items.append(
                {
                    "workflow_item_type": "deferred_decision",
                    "payment_record_id": item.payment_record_id,
                    "bank_transaction_id": item.bank_transaction_id,
                    "current_decision": {
                        "decision_id": item.id,
                        "decision_action": item.decision_action,
                        "decision_status": item.decision_status,
                        "reviewer_name": item.reviewer_name,
                    },
                    "available_actions": [
                        "accept",
                        "reject",
                        "write_off",
                        "mark_duplicate",
                        "manual_match_override",
                    ],
                }
            )

    return QueueResponse(
        run_id=run_id,
        queue_type=queue_type,
        count=len(shaped_items),
        items=shaped_items,
    )