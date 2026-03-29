from __future__ import annotations

from datetime import timedelta
import random

import pandas as pd

from .generator_config import GeneratorConfig


def generate_invoices(
    customers_df: pd.DataFrame,
    config: GeneratorConfig,
    rng: random.Random,
) -> pd.DataFrame:
    rows = []

    customer_records = customers_df.to_dict(orient="records")
    date_span_days = (config.invoice_end_date - config.invoice_start_date).days

    for i in range(1, config.n_invoices + 1):
        cust = rng.choice(customer_records)

        invoice_date = config.invoice_start_date + timedelta(days=rng.randint(0, date_span_days))
        payment_terms_days = rng.choices([7, 14, 30, 45], weights=[0.1, 0.2, 0.6, 0.1], k=1)[0]
        due_date = invoice_date + timedelta(days=payment_terms_days)

        amount = _generate_invoice_amount(config, rng)

        rows.append(
            {
                "invoice_id": f"INVREC-{i:06d}",
                "invoice_number": f"INV-{100000 + i}",
                "customer_id": cust["customer_id"],
                "customer_code": cust["customer_code"],
                "customer_name": cust["customer_name"],
                "invoice_date": invoice_date,
                "due_date": due_date,
                "invoice_amount": amount,
                "currency": config.currency,
            }
        )

    return pd.DataFrame(rows)


def _generate_invoice_amount(config: GeneratorConfig, rng: random.Random) -> float:
    use_common = rng.random() < config.common_amount_weight
    if use_common:
        amount = rng.choice(config.common_amount_values)
    else:
        amount = round(rng.uniform(50, 5000), 2)
    return float(amount)