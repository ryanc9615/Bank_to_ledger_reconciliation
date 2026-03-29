from __future__ import annotations

from datetime import timedelta
import random

import pandas as pd

from .generator_config import GeneratorConfig


def generate_payment_records(
    invoices_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    config: GeneratorConfig,
    rng: random.Random,
) -> pd.DataFrame:
    customer_lookup = customers_df.set_index("customer_id").to_dict(orient="index")
    rows = []

    for idx, invoice in enumerate(invoices_df.to_dict(orient="records"), start=1):
        customer = customer_lookup[invoice["customer_id"]]

        expected_payment_date = _expected_payment_date(
            due_date=invoice["due_date"],
            timing_profile=customer["payment_timing_profile"],
            rng=rng,
        )

        expected_reference = _build_expected_reference(
            invoice_number=invoice["invoice_number"],
            customer_code=invoice["customer_code"],
            rng=rng,
        )

        rows.append(
            {
                "payment_record_id": f"PAYREC-{idx:06d}",
                "invoice_id": invoice["invoice_id"],
                "customer_id": invoice["customer_id"],
                "customer_code": invoice["customer_code"],
                "customer_name": invoice["customer_name"],
                "invoice_number": invoice["invoice_number"],
                "expected_amount": invoice["invoice_amount"],
                "currency": invoice["currency"],
                "invoice_date": invoice["invoice_date"],
                "due_date": invoice["due_date"],
                "expected_payment_date": expected_payment_date,
                "expected_reference": expected_reference,
                "reference_quality_hint": customer["reference_reliability"],
                "scenario_type": "pending_generation",
            }
        )

    return pd.DataFrame(rows)


def _expected_payment_date(due_date, timing_profile: str, rng: random.Random):
    if timing_profile == "early":
        offset = rng.randint(-5, 0)
    elif timing_profile == "late":
        offset = rng.randint(1, 10)
    else:
        offset = rng.randint(-1, 3)
    return due_date + timedelta(days=offset)


def _build_expected_reference(invoice_number: str, customer_code: str, rng: random.Random) -> str:
    patterns = [
        invoice_number,
        f"{customer_code}-{invoice_number}",
        f"PAY {invoice_number}",
        f"{customer_code} {invoice_number[-6:]}"
    ]
    return rng.choice(patterns)