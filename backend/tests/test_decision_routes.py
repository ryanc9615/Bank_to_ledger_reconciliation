from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_run() -> dict:
    response = client.post(
        "/api/v1/reconciliation/runs",
        json={
            "parameters": {
                "date_tolerance_days": 5,
                "score_threshold": 0.95,
                "currency_required": True,
            }
        },
    )
    assert response.status_code == 200
    return response.json()


def get_first_review_item(run_id: str) -> dict:
    response = client.get(f"/api/v1/reconciliation/runs/{run_id}/queues/review")
    assert response.status_code == 200

    items = response.json()["items"]
    assert len(items) > 0, "Expected at least one review item for this test"

    return items[0]


def test_investigate_later_appears_in_deferred_queue():
    run = create_run()
    run_id = run["run_id"]
    review_item = get_first_review_item(run_id)

    payload = {
        "run_id": run_id,
        "payment_record_id": review_item["payment_record_id"],
        "bank_transaction_id": review_item["bank_transaction_id"],
        "match_candidate_id": review_item["candidate_id"],
        "decision_action": "investigate_later",
        "reviewer_name": "pytest",
        "review_comment": "defer test",
        "decision_reason_code": "needs_follow_up",
    }

    decision_response = client.post("/api/v1/decisions", json=payload)
    assert decision_response.status_code == 200

    decision = decision_response.json()
    assert decision["decision_action"] == "investigate_later"
    assert decision["decision_status"] == "deferred"
    assert decision["is_active"] is True

    deferred_response = client.get(
        f"/api/v1/reconciliation/runs/{run_id}/queues/deferred"
    )
    assert deferred_response.status_code == 200

    deferred_body = deferred_response.json()
    deferred_payment_ids = [
        item["payment_record_id"] for item in deferred_body["items"]
    ]

    assert review_item["payment_record_id"] in deferred_payment_ids


def test_accept_supersedes_deferred_and_removes_from_deferred_queue():
    run = create_run()
    run_id = run["run_id"]
    review_item = get_first_review_item(run_id)

    defer_payload = {
        "run_id": run_id,
        "payment_record_id": review_item["payment_record_id"],
        "bank_transaction_id": review_item["bank_transaction_id"],
        "match_candidate_id": review_item["candidate_id"],
        "decision_action": "investigate_later",
        "reviewer_name": "pytest",
        "review_comment": "defer first",
        "decision_reason_code": "needs_follow_up",
    }

    accept_payload = {
        "run_id": run_id,
        "payment_record_id": review_item["payment_record_id"],
        "bank_transaction_id": review_item["bank_transaction_id"],
        "match_candidate_id": review_item["candidate_id"],
        "decision_action": "accept",
        "reviewer_name": "pytest",
        "review_comment": "accept second",
        "decision_reason_code": "review_confirmed_match",
    }

    defer_response = client.post("/api/v1/decisions", json=defer_payload)
    assert defer_response.status_code == 200

    accept_response = client.post("/api/v1/decisions", json=accept_payload)
    assert accept_response.status_code == 200

    accept_data = accept_response.json()
    assert accept_data["decision_action"] == "accept"
    assert accept_data["decision_status"] == "resolved_matched"
    assert accept_data["is_active"] is True

    decisions_response = client.get(
        f"/api/v1/reconciliation/runs/{run_id}/decisions"
    )
    assert decisions_response.status_code == 200

    decisions = decisions_response.json()["items"]
    same_payment = [
        d for d in decisions
        if d["payment_record_id"] == review_item["payment_record_id"]
    ]
    active_same_payment = [d for d in same_payment if d["is_active"]]

    assert len(active_same_payment) == 1
    assert active_same_payment[0]["decision_action"] == "accept"

    deferred_response = client.get(
        f"/api/v1/reconciliation/runs/{run_id}/queues/deferred"
    )
    assert deferred_response.status_code == 200

    deferred_body = deferred_response.json()
    deferred_payment_ids = [
        item["payment_record_id"] for item in deferred_body["items"]
    ]

    assert review_item["payment_record_id"] not in deferred_payment_ids


def test_decision_creates_audit_log_row():
    run = create_run()
    run_id = run["run_id"]
    review_item = get_first_review_item(run_id)

    payload = {
        "run_id": run_id,
        "payment_record_id": review_item["payment_record_id"],
        "bank_transaction_id": review_item["bank_transaction_id"],
        "match_candidate_id": review_item["candidate_id"],
        "decision_action": "accept",
        "reviewer_name": "pytest",
        "review_comment": "audit log test",
        "decision_reason_code": "review_confirmed_match",
    }

    decision_response = client.post("/api/v1/decisions", json=payload)
    assert decision_response.status_code == 200

    audit_response = client.get(f"/api/v1/reconciliation/runs/{run_id}/audit-log")
    assert audit_response.status_code == 200

    audit_items = audit_response.json()["items"]
    assert len(audit_items) >= 1

    first = audit_items[0]
    assert "event_type" in first
    assert "actor_name" in first
    assert "request_payload" in first
    assert "evidence_snapshot" in first


def test_manual_override_requires_override_bank_id():
    run = create_run()
    run_id = run["run_id"]
    review_item = get_first_review_item(run_id)

    payload = {
        "run_id": run_id,
        "payment_record_id": review_item["payment_record_id"],
        "decision_action": "manual_match_override",
        "reviewer_name": "pytest",
        "review_comment": "missing override bank id",
        "decision_reason_code": "manual_override_selected",
    }

    response = client.post("/api/v1/decisions", json=payload)
    assert response.status_code == 400

    body = response.json()
    assert "detail" in body
    assert "manual_override_bank_transaction_id" in body["detail"]