"""Stable wrapper for PDF metadata extraction and cross-bid matching."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from bidsentry.forensics.metadata import compare_vendor_metadata, extract_pdf_metadata, parse_pdf_datetime


def fingerprint_document(pdf_bytes: bytes) -> dict[str, Any]:
    """Extract metadata fingerprints; this does not identify a document author."""
    return extract_pdf_metadata(pdf_bytes)


def match_vendor_metadata(vendors: list[dict[str, Any]], suspicious_minutes: int = 10) -> dict[str, Any]:
    return compare_vendor_metadata(vendors, suspicious_minutes=suspicious_minutes)


def compare_vendor_fingerprints(metadata_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare PDF metadata dictionaries for shared profiles and close submissions.

    Inputs may use PyMuPDF-style keys (``/CreationDate``, ``/Author``) or the
    normalized keys emitted by :func:`extract_pdf_metadata`.
    """

    vendors: list[dict[str, Any]] = []
    machine_values: dict[str, set[str]] = {}
    software_values: dict[str, set[str]] = {}
    for index, source in enumerate(metadata_list, 1):
        if not isinstance(source, dict):
            continue
        nested = source.get("document_metadata", source.get("metadata", source))
        raw = nested if isinstance(nested, dict) else source
        keys = {str(key).lstrip("/").casefold(): value for key, value in raw.items()}
        vendor_id = str(source.get("vendor_id") or source.get("file_id") or f"vendor-{index}")
        vendor_name = str(source.get("vendor_name") or source.get("filename") or vendor_id)
        metadata = {
            "author": _pick(keys, "author"),
            "creator": _pick(keys, "creator"),
            "producer": _pick(keys, "producer"),
            "creation_date": parse_pdf_datetime(_pick(keys, "creation_date", "creationdate")) or _pick(keys, "creation_date", "creationdate"),
            "modification_date": parse_pdf_datetime(_pick(keys, "modification_date", "moddate", "modificationdate")) or _pick(keys, "modification_date", "moddate", "modificationdate"),
            "document_uuid": _pick(keys, "document_uuid", "document_id", "trailer_id"),
            "document_uuid_sha256": _pick(keys, "document_uuid_sha256"),
            "system_uuid_sha256": _pick(keys, "system_uuid_sha256"),
            "font_fingerprints": _pick(keys, "font_fingerprints") or [],
        }
        machine = _pick(keys, "machine_fingerprint", "machine_id", "system_uuid", "system_id", "host_id")
        software = _pick(keys, "software_build", "build_version", "producer", "creator")
        vendors.append({
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "submission_timestamp": _parse_submission_time(
                _pick(source, "submission_timestamp", "submitted_at", "submission_time", "submitted_on")
            ),
            "document_metadata": metadata,
        })
        if machine is not None and str(machine).strip():
            machine_values.setdefault(str(machine).strip().casefold(), set()).add(vendor_id)
        if software is not None and str(software).strip():
            software_values.setdefault(str(software).strip().casefold(), set()).add(vendor_id)

    comparison = compare_vendor_metadata(vendors, suspicious_minutes=10)
    alerts = list(comparison["alerts"])
    names = {vendor["vendor_id"]: vendor["vendor_name"] for vendor in vendors}
    for machine_fingerprint, vendor_ids in sorted(machine_values.items()):
        if len(vendor_ids) < 2:
            continue
        alerts.append({
            "signal": "SHARED_MACHINE_FINGERPRINT",
            "vendor_ids": sorted(vendor_ids),
            "vendors": [names[vendor_id] for vendor_id in sorted(vendor_ids)],
            "fingerprint_sha256": hashlib.sha256(machine_fingerprint.encode("utf-8")).hexdigest(),
            "severity": "HIGH",
            "interpretation": "Fingerprint mesin yang sama adalah petunjuk untuk verifikasi sumber; tidak membuktikan kendali bersama.",
        })
    for software_fingerprint, vendor_ids in sorted(software_values.items()):
        if len(vendor_ids) < 2:
            continue
        alerts.append({
            "signal": "SHARED_SOFTWARE_BUILD",
            "vendor_ids": sorted(vendor_ids),
            "vendors": [names[vendor_id] for vendor_id in sorted(vendor_ids)],
            "fingerprint_sha256": hashlib.sha256(software_fingerprint.encode("utf-8")).hexdigest(),
            "severity": "LOW",
            "interpretation": "Build atau producer yang sama lazim terjadi dan hanya merupakan sinyal lemah.",
        })
    return {
        **comparison,
        "alerts": alerts,
        "compared_file_count": len(vendors),
        "submission_window_minutes": 10,
    }


def _pick(mapping: dict[str, Any], *keys: str) -> Any:
    normalized = {str(key).lstrip("/").casefold(): value for key, value in mapping.items()}
    return next((normalized[key.casefold()] for key in keys if key.casefold() in normalized), None)


def _parse_submission_time(value: Any) -> datetime | str | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return value.strip()
