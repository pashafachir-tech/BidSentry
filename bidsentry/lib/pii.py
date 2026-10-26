"""Small, conservative redaction helpers used before external processing."""

from __future__ import annotations

import re
from typing import Any


_PATTERNS = (
    (re.compile(r"\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b"), "[NPWP-REDACTED]"),
    (re.compile(r"\b\d{16}\b"), "[NIK-REDACTED]"),
    (re.compile(r"\b\d{10,15}\b"), "[NUMBER-REDACTED]"),
)


def mask_text(value: str) -> str:
    for pattern, replacement in _PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def mask_value(value: Any) -> Any:
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, dict):
        return {key: mask_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_value(item) for item in value]
    return value
