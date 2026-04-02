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


def test_dashboard_metrics_returns_expected_shape():
    response = client.get("/api/v1/metrics/dashboard")
    assert response.status_code == 200

    body = response.json()
    assert "total_runs" in body
    assert "completed_runs" in body
    assert "failed_runs" in body
    assert "latest_run_id" in body


def test_run_metrics_returns_expected_shape():
    run = create_run()
    run_id = run["run_id"]

    response = client.get(f"/api/v1/metrics/runs/{run_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["run_id"] == run_id
    assert "assigned_count" in body
    assert "auto_matched_count" in body
    assert "review_count" in body
    assert "unmatched_payment_count" in body
    assert "unmatched_bank_count" in body
    assert "decision_count" in body
    assert "deferred_count" in body
    assert "resolved_count" in body


def test_queue_metrics_returns_expected_shape():
    run = create_run()
    run_id = run["run_id"]

    response = client.get(f"/api/v1/metrics/runs/{run_id}/queues")
    assert response.status_code == 200

    body = response.json()
    assert body["run_id"] == run_id
    assert "auto_matched_count" in body
    assert "review_count" in body
    assert "unmatched_payment_count" in body
    assert "unmatched_bank_count" in body
    assert "deferred_count" in body