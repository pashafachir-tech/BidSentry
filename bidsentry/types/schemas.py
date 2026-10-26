"""Validated request schemas shared by API controllers."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any


class ValidationError(ValueError):
    def __init__(self, message: str, details: list[dict[str, str]] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or []


def _string(payload: dict[str, Any], key: str, *, aliases: tuple[str, ...] = (), maximum: int = 1_000_000) -> str:
    value: Any = payload.get(key)
    if value is None:
        for alias in aliases:
            if payload.get(alias) is not None:
                value = payload[alias]
                break
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"'{key}' must be a string.", [{"field": key, "issue": "expected_string"}])
    value = value.strip()
    if len(value) > maximum:
        raise ValidationError(f"'{key}' exceeds the {maximum:,} character limit.", [{"field": key, "issue": "too_long"}])
    return value


@dataclass(frozen=True)
class AuditRequest:
    package_name: str
    dok_pemilihan: str
    adendum: str
    pustaka: str
    allow_external_processing: bool = False
    review_role: str = "procurement"

    @classmethod
    def from_payload(cls, payload: Any) -> "AuditRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object.", [{"field": "$", "issue": "expected_object"}])
        package_name = _string(payload, "package_name", aliases=("nama_paket",), maximum=240) or "Audit dokumen baru"
        dok = _string(payload, "dok_pemilihan", aliases=("document_text",))
        addendum = _string(payload, "adendum", aliases=("addendum_text",))
        credentials = _string(payload, "pustaka", aliases=("credentials_text",))
        if not any((dok, addendum, credentials)):
            raise ValidationError(
                "Provide at least one document field: dok_pemilihan, adendum, or pustaka.",
                [{"field": "dok_pemilihan", "issue": "at_least_one_document_required"}],
            )
        consent = payload.get("allow_external_processing", False)
        if not isinstance(consent, bool):
            raise ValidationError("'allow_external_processing' must be a boolean.", [{"field": "allow_external_processing", "issue": "expected_boolean"}])
        review_role = payload.get("review_role", "procurement")
        if not isinstance(review_role, str) or review_role not in {"procurement", "legal"}:
            raise ValidationError("Pilih peran pengadaan atau hukum.", [{"field": "review_role", "issue": "invalid_value"}])
        return cls(package_name, dok, addendum, credentials, consent, review_role)

    def documents(self) -> dict[str, str]:
        return {"dok_pemilihan": self.dok_pemilihan, "adendum": self.adendum, "pustaka": self.pustaka}


@dataclass(frozen=True)
class DispatchRequest:
    payload: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Any) -> "DispatchRequest":
        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object.", [{"field": "$", "issue": "expected_object"}])
        allowed = {"nama_paket", "verdict", "risk_score", "alasan_utama", "catatan", "tender_id", "email_penerima", "allow_external_processing"}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValidationError("Ada kolom tindak lanjut yang tidak dikenal.", [{"field": key, "issue": "unknown_field"} for key in unknown])

        package_name = payload.get("nama_paket", "")
        if not isinstance(package_name, str) or not package_name.strip() or len(package_name) > 240:
            raise ValidationError("Nama paket wajib diisi dan maksimal 240 karakter.", [{"field": "nama_paket", "issue": "invalid_value"}])
        verdict = payload.get("verdict", "REVIEW_REQUIRED")
        if not isinstance(verdict, str) or len(verdict) > 80:
            raise ValidationError("Status review tidak valid.", [{"field": "verdict", "issue": "invalid_value"}])
        risk_score = payload.get("risk_score", 0)
        if isinstance(risk_score, bool) or not isinstance(risk_score, (int, float)) or not math.isfinite(float(risk_score)) or not 0 <= risk_score <= 100:
            raise ValidationError("Skor triase harus berupa angka 0–100.", [{"field": "risk_score", "issue": "out_of_range"}])
        reasons = payload.get("alasan_utama", payload.get("catatan", []))
        if isinstance(reasons, str):
            reasons = [reasons]
        if not isinstance(reasons, list) or len(reasons) > 5 or any(not isinstance(item, str) or len(item) > 500 for item in reasons):
            raise ValidationError("Ringkasan tindak lanjut maksimal berisi 5 teks, masing-masing 500 karakter.", [{"field": "alasan_utama", "issue": "invalid_value"}])
        tender_id = payload.get("tender_id", "")
        if not isinstance(tender_id, str) or len(tender_id) > 80:
            raise ValidationError("ID paket tidak valid.", [{"field": "tender_id", "issue": "invalid_value"}])
        consent = payload.get("allow_external_processing", False)
        if not isinstance(consent, bool):
            raise ValidationError("Persetujuan pengiriman harus berupa pilihan ya/tidak.", [{"field": "allow_external_processing", "issue": "expected_boolean"}])
        recipient = payload.get("email_penerima", "")
        if not isinstance(recipient, str) or len(recipient) > 254 or (recipient and not re.fullmatch(r"[^\s@]+@[^\s@]+", recipient.strip())):
            raise ValidationError("Alamat email penerima tidak valid.", [{"field": "email_penerima", "issue": "invalid_value"}])
        normalized = {
            "nama_paket": package_name.strip(),
            "verdict": verdict.strip() or "REVIEW_REQUIRED",
            "risk_score": risk_score,
            "alasan_utama": [item.strip() for item in reasons if item.strip()],
            "tender_id": tender_id.strip(),
            "email_penerima": recipient.strip(),
            "allow_external_processing": consent,
        }
        return cls(normalized)
