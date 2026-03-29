from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Sequence

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42
    output_dir: Path = REPO_ROOT / "data" / "synthetic" / "pack_b"

    currency: str = "GBP"

    n_customers: int = 75
    n_invoices: int = 2000

    invoice_start_date: date = date(2025, 1, 1)
    invoice_end_date: date = date(2025, 3, 31)

    matched_payment_rate: float = 0.82
    unexpected_bank_receipt_rate: float = 0.10
    reversal_rate: float = 0.02

    missing_reference_rate: float = 0.12
    truncated_reference_rate: float = 0.18

    max_reference_length: int = 18
    max_description_length: int = 40

    common_amount_values: Sequence[float] = field(
        default_factory=lambda: [
            99.0, 125.0, 149.0, 199.0, 250.0, 299.0, 399.0,
            500.0, 750.0, 999.0, 1200.0, 1500.0, 2500.0
        ]
    )
    common_amount_weight: float = 0.35

    lag_days_choices: Sequence[int] = field(
        default_factory=lambda: [-2, -1, 0, 1, 2, 3, 5, 7, 10]
    )
    lag_days_weights: Sequence[float] = field(
        default_factory=lambda: [0.03, 0.05, 0.18, 0.20, 0.18, 0.15, 0.10, 0.07, 0.04]
    )

    reference_reliability_levels: Sequence[str] = field(
        default_factory=lambda: ["high", "medium", "low"]
    )
    payment_timing_profiles: Sequence[str] = field(
        default_factory=lambda: ["early", "on_time", "late"]
    )


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)