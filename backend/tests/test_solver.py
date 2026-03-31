from app.matching.assignment.solver import (
    CandidateAssignmentView,
    solve_greedy_assignment,
)


def test_solver_selects_non_conflicting_candidates():
    candidates = [
        CandidateAssignmentView(
            candidate_id="c1",
            payment_record_id="p1",
            bank_transaction_id="b1",
            raw_score=0.97,
        ),
        CandidateAssignmentView(
            candidate_id="c2",
            payment_record_id="p2",
            bank_transaction_id="b2",
            raw_score=0.95,
        ),
    ]

    result = solve_greedy_assignment(candidates)

    assert result.selected_candidate_ids == ["c1", "c2"]
    assert result.rejected_candidate_ids == []


def test_solver_rejects_conflict_on_same_bank():
    candidates = [
        CandidateAssignmentView(
            candidate_id="c1",
            payment_record_id="p1",
            bank_transaction_id="b1",
            raw_score=0.97,
        ),
        CandidateAssignmentView(
            candidate_id="c2",
            payment_record_id="p2",
            bank_transaction_id="b1",
            raw_score=0.95,
        ),
    ]

    result = solve_greedy_assignment(candidates)

    assert result.selected_candidate_ids == ["c1"]
    assert result.rejected_candidate_ids == ["c2"]


def test_solver_rejects_conflict_on_same_payment():
    candidates = [
        CandidateAssignmentView(
            candidate_id="c1",
            payment_record_id="p1",
            bank_transaction_id="b1",
            raw_score=0.97,
        ),
        CandidateAssignmentView(
            candidate_id="c2",
            payment_record_id="p1",
            bank_transaction_id="b2",
            raw_score=0.95,
        ),
    ]

    result = solve_greedy_assignment(candidates)

    assert result.selected_candidate_ids == ["c1"]
    assert result.rejected_candidate_ids == ["c2"]


def test_solver_prefers_higher_score_first():
    candidates = [
        CandidateAssignmentView(
            candidate_id="c_low",
            payment_record_id="p1",
            bank_transaction_id="b1",
            raw_score=0.80,
        ),
        CandidateAssignmentView(
            candidate_id="c_high",
            payment_record_id="p2",
            bank_transaction_id="b1",
            raw_score=0.96,
        ),
    ]

    result = solve_greedy_assignment(candidates)

    assert result.selected_candidate_ids == ["c_high"]
    assert result.rejected_candidate_ids == ["c_low"]


def test_solver_filters_very_weak_candidates():
    candidates = [
        CandidateAssignmentView(
            candidate_id="c1",
            payment_record_id="p1",
            bank_transaction_id="b1",
            raw_score=0.49,
        ),
        CandidateAssignmentView(
            candidate_id="c2",
            payment_record_id="p2",
            bank_transaction_id="b2",
            raw_score=0.70,
        ),
    ]

    result = solve_greedy_assignment(candidates, minimum_score=0.50)

    assert result.selected_candidate_ids == ["c2"]
    assert result.rejected_candidate_ids == []