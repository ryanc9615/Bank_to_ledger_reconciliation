from __future__ import annotations

import csv
import io
from dataclasses import dataclass


class FileParsingError(Exception):
    pass


@dataclass
class ParsedCsvFile:
    headers: list[str]
    rows: list[dict[str, str]]
    total_rows: int


def parse_csv_bytes(file_bytes: bytes) -> ParsedCsvFile:
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileParsingError("File must be UTF-8 encoded CSV.") from exc

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise FileParsingError("CSV file is missing a header row.")

    headers = [header.strip() for header in reader.fieldnames]

    rows: list[dict[str, str]] = []
    for row in reader:
        cleaned_row = {
            (key.strip() if key else ""): (value.strip() if value is not None else "")
            for key, value in row.items()
        }
        rows.append(cleaned_row)

    return ParsedCsvFile(
        headers=headers,
        rows=rows,
        total_rows=len(rows),
    )


def validate_required_headers(headers: list[str], required_headers: set[str]) -> list[str]:
    header_set = {h.strip() for h in headers}
    missing = sorted(required_headers - header_set)
    return missing