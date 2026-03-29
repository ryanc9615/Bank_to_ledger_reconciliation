from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_csv(df: pd.DataFrame, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    df.to_csv(path, index=False)
    return path