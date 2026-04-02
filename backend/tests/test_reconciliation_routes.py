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


def test_start_run_returns_summary():
    data = create_run()

    assert "run_id" in data
    assert data["status"] in {"completed", "running"}
    assert "summary" in data

    summary = data["summary"]
    assert "candidate_count" in summary
    assert "assigned_count" in summary
    assert "auto_matched_count" in summary
    assert "review_count" in summary
    assert "unmatched_payment_count" in summary
    assert "unmatched_bank_count" in summary


def test_list_runs_returns_items():
    _ = create_run()

    response = client.get("/api/v1/reconciliation/runs")
    assert response.status_code == 200

    body = response.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 1


def test_invalid_queue_type_returns_400():
    run = create_run()
    run_id = run["run_id"]

    response = client.get(
        f"/api/v1/reconciliation/runs/{run_id}/queues/not_a_real_queue"
    )

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert "Unsupported queue type" in body["detail"]


def test_wrong_run_candidate_returns_404():
    run_1 = create_run()
    run_2 = create_run()

    proposals_response = client.get(
        f"/api/v1/reconciliation/runs/{run_1['run_id']}/proposals",
        params={"selected_only": "true"},
    )
    assert proposals_response.status_code == 200

    proposals = proposals_response.json()["items"]
    assert len(proposals) > 0

    candidate_id = proposals[0]["candidate_id"]

    wrong_run_response = client.get(
        f"/api/v1/reconciliation/runs/{run_2['run_id']}/proposals/{candidate_id}"
    )

    assert wrong_run_response.status_code == 404
    body = wrong_run_response.json()
    assert "detail" in body


def test_review_queue_returns_expected_shape():
    run = create_run()
    run_id = run["run_id"]

    response = client.get(f"/api/v1/reconciliation/runs/{run_id}/queues/review")
    assert response.status_code == 200

    body = response.json()
    assert body["run_id"] == run_id
    assert body["queue_type"] == "review"
    assert "count" in body
    assert "items" in body

    if body["items"]:
        item = body["items"][0]
        assert "workflow_item_type" in item
        assert "payment_record_id" in item
        assert "bank_transaction_id" in item
        assert "candidate_id" in item
        assert "available_actions" in item