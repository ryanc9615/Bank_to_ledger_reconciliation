from __future__ import annotations

import re
import string


_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")


def normalize_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return _WHITESPACE_RE.sub(" ", value)


def normalize_free_text(value: str | None) -> str | None:
    value = normalize_whitespace(value)
    if value is None:
        return None

    value = value.upper()
    value = value.replace("&", " AND ")
    value = _WHITESPACE_RE.sub(" ", value)
    return value.strip()


def normalize_reference_text(value: str | None) -> str | None:
    value = normalize_whitespace(value)
    if value is None:
        return None

    value = value.upper()
    value = value.translate(str.maketrans("", "", string.punctuation))
    value = _WHITESPACE_RE.sub("", value)
    return value or None


def normalize_name_text(value: str | None) -> str | None:
    value = normalize_free_text(value)
    if value is None:
        return None
    value = re.sub(r"[^\w\s]", " ", value)
    value = _WHITESPACE_RE.sub(" ", value)
    return value.strip() or None


def compact_alphanumeric(value: str | None) -> str | None:
    value = normalize_free_text(value)
    if value is None:
        return None
    value = _NON_ALNUM_RE.sub("", value)
    return value or None
