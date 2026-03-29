from __future__ import annotations

import pandas as pd


def validate_outputs(
    payment_records_df: pd.DataFrame,
    bank_transactions_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
) -> None:
    _assert_unique(payment_records_df, "payment_record_id")
    _assert_unique(bank_transactions_df, "bank_transaction_id")
    _assert_unique(ground_truth_df, "match_id")

    if ground_truth_df["payment_record_id"].duplicated().any():
        raise ValueError("A payment_record_id appears more than once in ground truth.")

    if ground_truth_df["bank_transaction_id"].duplicated().any():
        raise ValueError("A bank_transaction_id appears more than once in ground truth.")

    payment_ids = set(payment_records_df["payment_record_id"])
    bank_ids = set(bank_transactions_df["bank_transaction_id"])

    missing_payment_ids = set(ground_truth_df["payment_record_id"]) - payment_ids
    missing_bank_ids = set(ground_truth_df["bank_transaction_id"]) - bank_ids

    if missing_payment_ids:
        raise ValueError(f"Ground truth contains missing payment_record_ids: {sorted(list(missing_payment_ids))[:5]}")

    if missing_bank_ids:
        raise ValueError(f"Ground truth contains missing bank_transaction_ids: {sorted(list(missing_bank_ids))[:5]}")

    required_payment_cols = [
        "payment_record_id", "invoice_id", "customer_id", "expected_amount", "expected_payment_date"
    ]
    required_bank_cols = [
        "bank_transaction_id", "booking_date", "amount", "transaction_type"
    ]
    required_truth_cols = [
        "match_id", "payment_record_id", "bank_transaction_id"
    ]

    _assert_columns(payment_records_df, required_payment_cols, "payment_records_df")
    _assert_columns(bank_transactions_df, required_bank_cols, "bank_transactions_df")
    _assert_columns(ground_truth_df, required_truth_cols, "ground_truth_df")


def _assert_unique(df: pd.DataFrame, col: str) -> None:
    if df[col].duplicated().any():
        raise ValueError(f"Duplicate values found in {col}.")


def _assert_columns(df: pd.DataFrame, cols: list[str], df_name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{df_name} is missing required columns: {missing}")