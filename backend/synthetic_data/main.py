from __future__ import annotations

import random

from .bank_transactions import generate_bank_transactions_and_outcomes
from .customers import generate_customers
from .export import export_csv
from .generator_config import GeneratorConfig, ensure_output_dir
from .invoices import generate_invoices
from .payments import generate_payment_records
from .truth_builder import build_ground_truth_matches
from .validation import validate_outputs


def run_generator(config: GeneratorConfig | None = None) -> None:
    config = config or GeneratorConfig()
    ensure_output_dir(config.output_dir)

    rng = random.Random(config.seed)

    customers_df = generate_customers(config, rng)
    invoices_df = generate_invoices(customers_df, config, rng)
    payment_records_df = generate_payment_records(invoices_df, customers_df, config, rng)

    bank_transactions_df, payment_records_outcomes_df = generate_bank_transactions_and_outcomes(
        payment_records_df=payment_records_df,
        config=config,
        rng=rng,
    )

    ground_truth_df = build_ground_truth_matches(payment_records_outcomes_df)

    # Export clean V1 files
    export_payment_records_df = payment_records_outcomes_df.drop(columns=["matched_bank_transaction_id"])
    export_bank_transactions_df = bank_transactions_df.copy()

    validate_outputs(
        payment_records_df=export_payment_records_df,
        bank_transactions_df=export_bank_transactions_df,
        ground_truth_df=ground_truth_df,
    )

    export_csv(export_payment_records_df, config.output_dir, "payment_records.csv")
    export_csv(export_bank_transactions_df, config.output_dir, "bank_transactions.csv")
    export_csv(ground_truth_df, config.output_dir, "ground_truth_matches.csv")

    print("Synthetic data generation complete.")
    print(f"Output directory: {config.output_dir}")
    print(f"Customers: {len(customers_df)}")
    print(f"Invoices / Payment Records: {len(export_payment_records_df)}")
    print(f"Bank Transactions: {len(export_bank_transactions_df)}")
    print(f"Ground Truth Matches: {len(ground_truth_df)}")


if __name__ == "__main__":
    run_generator()