from __future__ import annotations

import pandas as pd


def build_ground_truth_matches(payment_records_df: pd.DataFrame) -> pd.DataFrame:
    matched = payment_records_df[payment_records_df["matched_bank_transaction_id"].notna()].copy()

    truth = matched[["payment_record_id", "matched_bank_transaction_id"]].rename(
        columns={"matched_bank_transaction_id": "bank_transaction_id"}
    )

    truth.insert(0, "match_id", [f"MATCH-{i:07d}" for i in range(1, len(truth) + 1)])
    truth["match_type"] = "one_to_one"
    truth["match_status"] = "matched"

    return truth