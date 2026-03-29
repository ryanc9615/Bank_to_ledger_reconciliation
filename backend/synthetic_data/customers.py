from __future__ import annotations

from dataclasses import dataclass
import random
from typing import List

import pandas as pd

from .generator_config import GeneratorConfig


@dataclass(frozen=True)
class Customer:
    customer_id: str
    customer_code: str
    customer_name: str
    segment: str
    reference_reliability: str
    payment_timing_profile: str


CUSTOMER_NAME_PREFIXES = [
    "Acme", "Northstar", "BlueRock", "Silverline", "Harbour", "Vertex",
    "Redwood", "Summit", "BrightPath", "ClearWater", "Maple", "IronBridge"
]

CUSTOMER_NAME_SUFFIXES = [
    "Ltd", "Limited", "Group", "Holdings", "Services", "Trading",
    "Solutions", "Retail", "Distribution", "Partners"
]

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]


def generate_customers(config: GeneratorConfig, rng: random.Random) -> pd.DataFrame:
    rows: List[dict] = []

    used_names = set()
    for i in range(1, config.n_customers + 1):
        name = _unique_customer_name(rng, used_names)
        rows.append(
            {
                "customer_id": f"CUST-{i:05d}",
                "customer_code": f"C{i:04d}",
                "customer_name": name,
                "segment": rng.choices(SEGMENTS, weights=[0.6, 0.3, 0.1], k=1)[0],
                "reference_reliability": rng.choices(
                    config.reference_reliability_levels,
                    weights=[0.45, 0.40, 0.15],
                    k=1,
                )[0],
                "payment_timing_profile": rng.choices(
                    config.payment_timing_profiles,
                    weights=[0.15, 0.65, 0.20],
                    k=1,
                )[0],
            }
        )

    return pd.DataFrame(rows)


def _unique_customer_name(rng: random.Random, used_names: set[str]) -> str:
    while True:
        name = f"{rng.choice(CUSTOMER_NAME_PREFIXES)} {rng.choice(CUSTOMER_NAME_SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            return name