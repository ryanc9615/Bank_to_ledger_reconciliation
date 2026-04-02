from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match_decision import MatchDecision
from app.models.reconciliation_run import ReconciliationRun


class MetricsService:
    def get_dashboard_metrics(self, db: Session) -> dict:
        total_runs = db.scalar(select(func.count()).select_from(ReconciliationRun)) or 0
        completed_runs = db.scalar(
            select(func.count()).select_from(ReconciliationRun).where(ReconciliationRun.status == "completed")
        ) or 0
        failed_runs = db.scalar(
            select(func.count()).select_from(ReconciliationRun).where(ReconciliationRun.status == "failed")
        ) or 0

        latest_run = db.execute(
            select(ReconciliationRun)
            .order_by(ReconciliationRun.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "latest_run_id": latest_run.id if latest_run else None,
            "latest_run_auto_matched_count": getattr(latest_run, "auto_matched_count", 0) if latest_run else 0,
            "latest_run_review_count": getattr(latest_run, "review_count", 0) if latest_run else 0,
            "latest_run_unmatched_payment_count": getattr(latest_run, "unmatched_payment_count", 0) if latest_run else 0,
            "latest_run_unmatched_bank_count": getattr(latest_run, "unmatched_bank_count", 0) if latest_run else 0,
        }

    def get_run_metrics(self, db: Session, run_id) -> dict:
        run = db.execute(
            select(ReconciliationRun).where(ReconciliationRun.id == run_id)
        ).scalar_one()

        decision_count = db.scalar(
            select(func.count()).select_from(MatchDecision).where(MatchDecision.run_id == run_id)
        ) or 0

        deferred_count = db.scalar(
            select(func.count()).select_from(MatchDecision).where(
                MatchDecision.run_id == run_id,
                MatchDecision.is_active.is_(True),
                MatchDecision.decision_status == "deferred",
            )
        ) or 0

        resolved_count = db.scalar(
            select(func.count()).select_from(MatchDecision).where(
                MatchDecision.run_id == run_id,
                MatchDecision.is_active.is_(True),
                MatchDecision.decision_status != "deferred",
            )
        ) or 0

        return {
            "run_id": run.id,
            "assigned_count": getattr(run, "assigned_count", 0),
            "auto_matched_count": getattr(run, "auto_matched_count", 0),
            "review_count": getattr(run, "review_count", 0),
            "unmatched_payment_count": getattr(run, "unmatched_payment_count", 0),
            "unmatched_bank_count": getattr(run, "unmatched_bank_count", 0),
            "decision_count": decision_count,
            "deferred_count": deferred_count,
            "resolved_count": resolved_count,
        }

    def get_queue_metrics(self, db: Session, run_id) -> dict:
        run = db.execute(
            select(ReconciliationRun).where(ReconciliationRun.id == run_id)
        ).scalar_one()

        deferred_count = db.scalar(
            select(func.count()).select_from(MatchDecision).where(
                MatchDecision.run_id == run_id,
                MatchDecision.is_active.is_(True),
                MatchDecision.decision_status == "deferred",
            )
        ) or 0

        return {
            "run_id": run.id,
            "auto_matched_count": getattr(run, "auto_matched_count", 0),
            "review_count": getattr(run, "review_count", 0),
            "unmatched_payment_count": getattr(run, "unmatched_payment_count", 0),
            "unmatched_bank_count": getattr(run, "unmatched_bank_count", 0),
            "deferred_count": deferred_count,
        }