"""Small, conservative redaction helpers used before external processing."""

from __future__ import annotations

import re
from typing import Any


_PATTERNS = (
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL-REDACTED]"),
    # Indonesian phone numbers (+62, 62, 08)
    (re.compile(r"(?:\+62[\s.-]?|\b62[\s.-]?|\b0)8[1-9](?:[0-9\s.-]{5,11}[0-9])\b"), "[PHONE-REDACTED]"),
    # Bank account numbers with label (e.g. Rek. BCA 1234567890, No. Rekening 12345678)
    (re.compile(r"(?i)\b((?:(?:no\.?\s*)?rek(?:\.|ening)?|rekening(?:\s+bank)?)(?:[\s\w.]{0,25}?)[:#.]?\s*)(\d{8,18})\b"), r"\1[ACCOUNT-REDACTED]"),
    # Formatted NPWP
    (re.compile(r"\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b"), "[NPWP-REDACTED]"),
    # Unformatted NPWP with label
    (re.compile(r"(?i)\b(NPWP(?:[\s\w]{0,25}?)[:#.]?\s*)(\d{15,16})\b"), r"\1[NPWP-REDACTED]"),
    # NIK with label (including role labels like NIK Direktur/Pengurus/Pemohon)
    (re.compile(r"(?i)\b((?:NIK|KTP|no\.?\s*identitas)(?:[\s\w]{0,25}?)[:#.]?\s*)(\d{16})\b"), r"\1[NIK-REDACTED]"),
    # Standalone 16-digit Indonesian NIK
    (re.compile(r"\b[1-9]\d{15}\b"), "[NIK-REDACTED]"),
    # 10-15 digit identifier strictly near indicator labels (never bare money amounts)
    (re.compile(r"(?i)\b((?:NPWP|NIK|KTP|telp(?:on)?|hp|wa|rek(?:\.|ening)?)(?:[\s\w]{0,25}?)[:#.]?\s*)(\d{10,15})\b"), r"\1[NUMBER-REDACTED]"),
)


def contains_unmasked_pii(text: str) -> bool:
    """Return True if text contains recognizable unmasked PII patterns."""
    if not isinstance(text, str) or not text:
        return False
    for pattern, _ in _PATTERNS:
        if pattern.search(text):
            return True
    return False


def count_redacted_pii(text: str) -> int:
    """Count how many PII entities (NIK, NPWP, Rekening, Telp, Email) match in text."""
    if not isinstance(text, str) or not text:
        return 0
    total = 0
    for pattern, _ in _PATTERNS:
        total += len(pattern.findall(text))
    return total


def mask_text(value: str) -> str:
    if not isinstance(value, str) or not value:
        return value
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


def recover_unmasked_quote(quote: str, original_text: str) -> str | None:
    """Map a potentially redacted quote back to its verbatim equivalent in original_text."""
    if not isinstance(quote, str) or not quote:
        return None
    if quote in original_text:
        return quote
    if "REDACTED]" in quote:
        pattern = re.escape(quote)
        pattern = re.sub(r'\\\[[A-Za-z0-9_\\-]+REDACTED\\\]', lambda _: r'[\s\S]{1,60}?', pattern)
        try:
            m = re.search(pattern, original_text)
            if m:
                return m.group(0)
        except re.error:
            pass
    return None
