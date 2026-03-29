from __future__ import annotations

from pathlib import Path
import pandas as pd


def run_validation_report(base_dir: Path | None = None) -> None:
    if base_dir is None:
        repo_root = Path(__file__).resolve().parents[2]
        base_dir = repo_root / "data" / "synthetic" / "pack_b"

    payments_path = base_dir / "payment_records.csv"
    bank_path = base_dir / "bank_transactions.csv"
    truth_path = base_dir / "ground_truth_matches.csv"

    payments = pd.read_csv(payments_path)
    bank = pd.read_csv(bank_path)
    truth = pd.read_csv(truth_path)

    print("=== PACK B VALIDATION REPORT ===")
    print()
    print("Row counts")
    print(f"payment_records:       {len(payments)}")
    print(f"bank_transactions:     {len(bank)}")
    print(f"ground_truth_matches:  {len(truth)}")
    print()

    print("Payment record scenario mix")
    print(payments["scenario_type"].value_counts(dropna=False))
    print()

    print("Bank scenario mix")
    print(bank["scenario_type"].value_counts(dropna=False))
    print()

    print("Bank transaction type mix")
    print(bank["transaction_type"].value_counts(dropna=False))
    print()

    reversal_rate = (bank["amount"] < 0).mean()
    missing_ref_rate_all = (bank["payer_reference"].fillna("") == "").mean()

    print(f"Reversal rate (all bank rows): {reversal_rate:.4%}")
    print(f"Missing reference rate (all bank rows): {missing_ref_rate_all:.4%}")
    print()

    matched_bank = bank[bank["transaction_type"] == "credit"].copy()
    missing_ref_rate_matched = (matched_bank["payer_reference"].fillna("") == "").mean()

    print("Matched bank credit noise mix")
    print(matched_bank["scenario_type"].value_counts(dropna=False))
    print()
    print(f"Missing reference rate (matched credits only): {missing_ref_rate_matched:.4%}")
    print()

    duplicated_payment_ids = truth["payment_record_id"].duplicated().sum()
    duplicated_bank_ids = truth["bank_transaction_id"].duplicated().sum()

    print("Ground truth integrity")
    print(f"Duplicated payment_record_id in truth: {duplicated_payment_ids}")
    print(f"Duplicated bank_transaction_id in truth: {duplicated_bank_ids}")
    print()

    amount_counts = payments["expected_amount"].value_counts()
    duplicate_amount_values = (amount_counts > 1).sum()

    print("Duplicate amount profile")
    print(f"Distinct expected_amount values repeated more than once: {duplicate_amount_values}")
    print(amount_counts.head(20))
    print()

    print("Validation report complete.")


if __name__ == "__main__":
    run_validation_report()