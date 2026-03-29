from __future__ import annotations

from datetime import timedelta
import random

import pandas as pd

from .generator_config import GeneratorConfig
from .noise_injection import apply_reference_noise


def generate_bank_transactions_and_outcomes(
    payment_records_df: pd.DataFrame,
    config: GeneratorConfig,
    rng: random.Random,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
        bank_transactions_df, payment_records_with_outcomes_df
    """
    payment_rows = payment_records_df.to_dict(orient="records")
    bank_rows = []
    updated_payment_rows = []
    tx_counter = 1

    for pay in payment_rows:
        matched = rng.random() < config.matched_payment_rate

        if matched:
            booking_date = _apply_date_lag(pay["expected_payment_date"], config, rng)
            payer_reference, noise_type = apply_reference_noise(
                expected_reference=pay["expected_reference"],
                rng=rng,
                missing_rate=config.missing_reference_rate,
                truncated_rate=config.truncated_reference_rate,
                max_length=config.max_reference_length,
            )

            payer_name = _variant_payer_name(pay["customer_name"], rng)
            description = _build_bank_description(
                payer_name=payer_name,
                payer_reference=payer_reference,
                max_length=config.max_description_length,
            )

            bank_transaction_id = f"BTX-{tx_counter:07d}"
            tx_counter += 1

            bank_rows.append(
                {
                    "bank_transaction_id": bank_transaction_id,
                    "booking_date": booking_date,
                    "value_date": booking_date,
                    "amount": pay["expected_amount"],
                    "currency": pay["currency"],
                    "transaction_type": "credit",
                    "payer_name": payer_name,
                    "payer_reference": payer_reference,
                    "bank_description": description,
                    "scenario_type": noise_type,
                    "is_reversal": False,
                    "original_bank_transaction_id": None,
                }
            )

            pay["scenario_type"] = "matched"
            pay["matched_bank_transaction_id"] = bank_transaction_id
        else:
            pay["scenario_type"] = "unmatched_expected"
            pay["matched_bank_transaction_id"] = None

        updated_payment_rows.append(pay)

    bank_df = pd.DataFrame(bank_rows)
    payment_outcomes_df = pd.DataFrame(updated_payment_rows)

    bank_df, payment_outcomes_df = _inject_unexpected_receipts(
        bank_df=bank_df,
        payment_records_df=payment_outcomes_df,
        config=config,
        rng=rng,
        tx_counter_start=tx_counter,
    )

    bank_df = _inject_reversals(bank_df=bank_df, config=config, rng=rng)

    return bank_df.sort_values("booking_date").reset_index(drop=True), payment_outcomes_df


def _apply_date_lag(expected_payment_date, config: GeneratorConfig, rng: random.Random):
    lag = rng.choices(config.lag_days_choices, weights=config.lag_days_weights, k=1)[0]
    return expected_payment_date + timedelta(days=lag)


def _variant_payer_name(customer_name: str, rng: random.Random) -> str:
    variants = [
        customer_name,
        customer_name.upper(),
        customer_name.replace("Limited", "Ltd"),
        customer_name.replace("Ltd", "LIMITED"),
    ]
    return rng.choice(variants)


def _build_bank_description(payer_name: str, payer_reference: str, max_length: int) -> str:
    if payer_reference:
        desc = f"{payer_name} {payer_reference}"
    else:
        desc = payer_name
    return desc[:max_length]


def _inject_unexpected_receipts(
    bank_df: pd.DataFrame,
    payment_records_df: pd.DataFrame,
    config: GeneratorConfig,
    rng: random.Random,
    tx_counter_start: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_unexpected = int(config.n_invoices * config.unexpected_bank_receipt_rate)

    rows = []
    tx_counter = tx_counter_start
    customer_rows = payment_records_df[["customer_name", "customer_code"]].drop_duplicates().to_dict(orient="records")

    for _ in range(n_unexpected):
        maybe_known = rng.random() < 0.6
        if maybe_known and customer_rows:
            cust = rng.choice(customer_rows)
            payer_name = cust["customer_name"]
            payer_reference = rng.choice([
                "",
                cust["customer_code"],
                f"MISC {cust['customer_code']}",
                "ON ACCOUNT",
                "ADVANCE PAYMENT",
            ])
        else:
            payer_name = rng.choice(["Unknown Sender", "Misc Credit", "Legacy Payer", "Third Party Receipt"])
            payer_reference = rng.choice(["", "TRANSFER", "PAYMENT", "MISC"])

        booking_date = rng.choice(payment_records_df["expected_payment_date"].tolist())
        amount = _unexpected_amount(config, rng)

        rows.append(
            {
                "bank_transaction_id": f"BTX-{tx_counter:07d}",
                "booking_date": booking_date,
                "value_date": booking_date,
                "amount": amount,
                "currency": config.currency,
                "transaction_type": "unexpected_credit",
                "payer_name": payer_name,
                "payer_reference": payer_reference[: config.max_reference_length],
                "bank_description": f"{payer_name} {payer_reference}".strip()[: config.max_description_length],
                "scenario_type": "unexpected_receipt",
                "is_reversal": False,
                "original_bank_transaction_id": None,
            }
        )
        tx_counter += 1

    combined = pd.concat([bank_df, pd.DataFrame(rows)], ignore_index=True)
    return combined, payment_records_df


def _unexpected_amount(config: GeneratorConfig, rng: random.Random) -> float:
    if rng.random() < 0.5:
        return float(rng.choice(config.common_amount_values))
    return round(rng.uniform(50, 5000), 2)


def _inject_reversals(bank_df: pd.DataFrame, config: GeneratorConfig, rng: random.Random) -> pd.DataFrame:
    if bank_df.empty:
        return bank_df

    eligible = bank_df[(bank_df["transaction_type"] == "credit") & (~bank_df["is_reversal"])]
    if eligible.empty:
        return bank_df

    target_n_reversals = max(1, int(len(bank_df) * config.reversal_rate))
    n_reversals = min(target_n_reversals, len(eligible))

    selected = eligible.sample(n=n_reversals, random_state=rng.randint(1, 10_000))
    reversal_rows = []

    next_numeric = (
        bank_df["bank_transaction_id"]
        .str.replace("BTX-", "", regex=False)
        .astype(int)
        .max()
        + 1
    )

    for _, row in selected.iterrows():
        lag_days = rng.randint(1, 14)
        reversal_date = row["booking_date"] + timedelta(days=lag_days)

        reversal_rows.append(
            {
                "bank_transaction_id": f"BTX-{next_numeric:07d}",
                "booking_date": reversal_date,
                "value_date": reversal_date,
                "amount": -float(row["amount"]),
                "currency": row["currency"],
                "transaction_type": "reversal",
                "payer_name": row["payer_name"],
                "payer_reference": (f"REV {row['payer_reference']}" if row["payer_reference"] else "REVERSAL")[:config.max_reference_length],
                "bank_description": f"REVERSAL {row['bank_transaction_id']}"[: config.max_description_length],
                "scenario_type": "reversal",
                "is_reversal": True,
                "original_bank_transaction_id": row["bank_transaction_id"],
            }
        )
        next_numeric += 1

    combined = pd.concat([bank_df, pd.DataFrame(reversal_rows)], ignore_index=True)
    return combined