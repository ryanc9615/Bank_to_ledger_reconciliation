from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decision_audit_log import DecisionAuditLog
from app.models.match_candidate import MatchCandidate
from app.models.match_decision import MatchDecision
from app.schemas.decisions import DecisionCreateRequest
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, status
from decimal import Decimal


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decision_audit_log import DecisionAuditLog
from app.models.match_candidate import MatchCandidate
from app.models.match_decision import MatchDecision
from app.schemas.decisions import DecisionCreateRequest


class DecisionService:
    ACTION_TO_STATUS = {
        "accept": "resolved_matched",
        "reject": "resolved_unmatched",
        "write_off": "resolved_write_off",
        "investigate_later": "deferred",
        "mark_duplicate": "resolved_duplicate",
        "manual_match_override": "resolved_matched",
    }

    def submit_decision(self, db: Session, request: DecisionCreateRequest) -> MatchDecision:
        if request.decision_action == "manual_match_override" and not request.manual_override_bank_transaction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="manual_override_bank_transaction_id is required for manual_match_override",
            )

        existing_active_rows = list(
            db.execute(
                select(MatchDecision).where(
                    MatchDecision.run_id == request.run_id,
                    MatchDecision.payment_record_id == request.payment_record_id,
                    MatchDecision.is_active.is_(True),
                )
            ).scalars().all()
        )

        evidence_snapshot = self._build_evidence_snapshot(db=db, request=request)

        decision = MatchDecision(
            run_id=request.run_id,
            payment_record_id=request.payment_record_id,
            bank_transaction_id=request.manual_override_bank_transaction_id or request.bank_transaction_id,
            match_candidate_id=request.match_candidate_id,
            decision_action=request.decision_action,
            decision_status=self.ACTION_TO_STATUS[request.decision_action],
            reviewer_name=request.reviewer_name,
            review_comment=request.review_comment,
            decision_reason_code=request.decision_reason_code,
            evidence_snapshot=evidence_snapshot,
            is_active=True,
        )
        db.add(decision)
        db.flush()

        before_state = None
        if existing_active_rows:
            before_state = jsonable_encoder(
                [self._serialize_decision(existing) for existing in existing_active_rows]
            )
            for existing in existing_active_rows:
                existing.is_active = False
                existing.superseded_by_decision_id = decision.id

        after_state = jsonable_encoder(self._serialize_decision(decision))
        request_payload = jsonable_encoder(request.model_dump(mode="json"))

        audit = DecisionAuditLog(
            decision_id=decision.id,
            run_id=request.run_id,
            payment_record_id=request.payment_record_id,
            bank_transaction_id=decision.bank_transaction_id,
            match_candidate_id=request.match_candidate_id,
            event_type="decision_created" if not existing_active_rows else "decision_superseded",
            actor_name=request.reviewer_name,
            before_state=before_state,
            after_state=after_state,
            request_payload=request_payload,
            evidence_snapshot=jsonable_encoder(evidence_snapshot),
            notes=request.review_comment,
        )
        db.add(audit)
        db.commit()
        db.refresh(decision)
        return decision

    def list_run_decisions(self, db: Session, run_id) -> list[MatchDecision]:
        results = db.execute(
            select(MatchDecision)
            .where(MatchDecision.run_id == run_id)
            .order_by(MatchDecision.created_at.desc())
        )
        return list(results.scalars().all())

    def list_run_audit_log(self, db: Session, run_id) -> list[DecisionAuditLog]:
        results = db.execute(
            select(DecisionAuditLog)
            .where(DecisionAuditLog.run_id == run_id)
            .order_by(DecisionAuditLog.event_timestamp.desc())
        )
        return list(results.scalars().all())

    def _build_evidence_snapshot(self, db: Session, request: DecisionCreateRequest) -> dict | None:
        if not request.match_candidate_id:
            return jsonable_encoder({
                "decision_basis": "no_candidate_snapshot",
                "manual_override_bank_transaction_id": (
                    str(request.manual_override_bank_transaction_id)
                    if request.manual_override_bank_transaction_id
                    else None
                ),
            })

        candidate = db.execute(
            select(MatchCandidate).where(MatchCandidate.id == request.match_candidate_id)
        ).scalar_one_or_none()

        if not candidate:
            return jsonable_encoder({"decision_basis": "candidate_not_found"})

        snapshot = {
            "candidate_id": str(candidate.id),
            "raw_score": getattr(candidate, "raw_score", None),
            "route_status": getattr(candidate, "route_status", None),
            "selected": getattr(candidate, "selected", None),
            "score_reasons": getattr(candidate, "score_reasons", []) or [],
            "score_warnings": getattr(candidate, "score_warnings", []) or [],
            "guardrail_flags": getattr(candidate, "guardrail_flags", {}) or {},
        }

        return jsonable_encoder(snapshot)

    def _serialize_decision(self, decision: MatchDecision) -> dict:
        payload = {
            "id": str(decision.id),
            "run_id": str(decision.run_id),
            "payment_record_id": str(decision.payment_record_id),
            "bank_transaction_id": str(decision.bank_transaction_id) if decision.bank_transaction_id else None,
            "match_candidate_id": str(decision.match_candidate_id) if decision.match_candidate_id else None,
            "decision_action": decision.decision_action,
            "decision_status": decision.decision_status,
            "reviewer_name": decision.reviewer_name,
            "review_comment": decision.review_comment,
            "decision_reason_code": decision.decision_reason_code,
            "is_active": decision.is_active,
        }
        return jsonable_encoder(payload)
    
    def _to_jsonable(self, value):
        return jsonable_encoder(
            value,
            custom_encoder={
                Decimal: float,
        },
    )