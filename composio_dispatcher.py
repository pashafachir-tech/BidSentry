#!/usr/bin/env python3
"""
BidSentry — Composio Dispatcher
=================================
Executes 3 workspace actions via the Composio REST API for each completed
audit dossier:

  1. GOOGLEDOCS_CREATE_DOCUMENT  — Official audit dossier document
  2. GOOGLECALENDAR_CREATE_EVENT — Aanwijzing clarification deadline (H+7)
  3. GMAIL_CREATE_EMAIL_DRAFT    — Legal team verification email draft

All I/O uses Python stdlib only (urllib.request, json, os, datetime).
No third-party pip dependencies are required.

Environment:
    COMPOSIO_API_KEY  — Composio API key (required for live mode)
                        Falls back to reading .env file if not set in env.

Usage (standalone test):
    python composio_dispatcher.py
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ─── Configuration ────────────────────────────────────────────────────────────

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v1/actions/{action}/execute"
REQUEST_TIMEOUT   = 30   # seconds per Composio API call
ENTITY_ID         = "default"


# ─── .env loader (stdlib, no python-dotenv needed) ────────────────────────────

def _load_dotenv(env_path: Path | None = None) -> None:
    """
    Parse a .env file and inject values into os.environ for any key not
    already present. Silently skips if the file does not exist.
    """
    path = env_path or (Path(__file__).parent / ".env")
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _get_api_key() -> str | None:
    """Return the Composio API key, loading .env if needed."""
    _load_dotenv()
    return os.environ.get("COMPOSIO_API_KEY", "").strip() or None


# ─── Low-level HTTP helper ────────────────────────────────────────────────────

def _post_composio(action: str, api_key: str, params: dict) -> dict:
    """
    POST to the Composio execute endpoint for *action*.
    Returns the parsed JSON response dict.
    Raises urllib.error.URLError / urllib.error.HTTPError on network failure.
    """
    url     = COMPOSIO_BASE_URL.format(action=action)
    payload = json.dumps({
        "entityId":    ENTITY_ID,
        "appName":     action.split("_")[0].upper(),
        "actionName":  action,
        "input":       params,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data    = payload,
        method  = "POST",
        headers = {
            "Content-Type":  "application/json",
            "Accept":        "application/json",
            "x-api-key":     api_key,
        },
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── Fallback simulation (used when API key is absent or request fails) ───────

def _simulate_result(action: str, audit_data: dict) -> dict:
    """
    Return a realistic-looking simulated payload so the server never crashes
    when the live Composio API is unavailable.
    """
    package_name = audit_data.get("nama_paket", "Pengadaan Jasa Konsultansi Portal Satu Data")
    now          = datetime.now(tz=timezone(timedelta(hours=7)))  # WIB
    h7           = now + timedelta(days=7)

    sims = {
        "GOOGLEDOCS_CREATE_DOCUMENT": {
            "documentId": "SIMULATED-DOC-001",
            "documentUrl": "https://docs.google.com/document/d/SIMULATED-DOC-001/edit",
            "title": f"BidSentry Audit Dossier - {package_name}",
            "createdAt": now.isoformat(),
        },
        "GOOGLECALENDAR_CREATE_EVENT": {
            "eventId": "SIMULATED-EVENT-001",
            "eventUrl": "https://calendar.google.com/calendar/event?eid=SIMULATED-EVENT-001",
            "summary": f"[BidSentry] Batas Klarifikasi Aanwijzing — {package_name}",
            "start": h7.replace(hour=9,  minute=0,  second=0).isoformat(),
            "end":   h7.replace(hour=10, minute=0,  second=0).isoformat(),
        },
        "GMAIL_CREATE_EMAIL_DRAFT": {
            "draftId": "SIMULATED-DRAFT-001",
            "draftUrl": "https://mail.google.com/mail/#drafts/SIMULATED-DRAFT-001",
            "subject": f"[BidSentry] Instruksi Verifikasi Klausul — {package_name}",
            "createdAt": now.isoformat(),
        },
    }
    return {"success": True, "simulated": True, "data": sims.get(action, {})}


# ─── Action builders ──────────────────────────────────────────────────────────

def _build_docs_params(audit_data: dict) -> dict:
    """Build the input dict for GOOGLEDOCS_CREATE_DOCUMENT."""
    package_name   = audit_data.get("nama_paket", "Pengadaan Jasa Konsultansi Portal Satu Data")
    verdict        = audit_data.get("verdict", "GO-WITH-CAUTION")
    risk_score     = audit_data.get("risk_score", "TINGGI")
    poison_pills   = audit_data.get("temuan_klausul_beracun", [])
    compliance     = audit_data.get("matriks_kepatuhan", [])
    alasan         = audit_data.get("alasan_utama", [])
    now_str        = datetime.now(tz=timezone(timedelta(hours=7))).strftime("%d %B %Y %H:%M WIB")

    # Format poison-pill section
    pp_lines = []
    for pp in poison_pills:
        pp_lines.append(
            f"• {pp.get('pasal', '')}\n"
            f"  Jenis Risiko : {pp.get('jenis_risiko', '')}\n"
            f"  Pelanggaran  : {pp.get('pelanggaran_regulasi', '')}\n"
            f"  Mitigasi     : {pp.get('saran_mitigasi', '')}"
        )

    # Format compliance matrix section
    matrix_lines = []
    for row in compliance:
        matrix_lines.append(
            f"[{row.get('status', '')}] {row.get('id_syarat', '')} — {row.get('kategori', '')}: "
            f"{row.get('klausul_resmi', '')[:120]}..."
        )

    body = "\n\n".join([
        f"BIDSENTRY AUDIT DOSSIER",
        f"Paket   : {package_name}",
        f"Dibuat  : {now_str}",
        f"Verdik  : {verdict}",
        f"Risiko  : {risk_score}",
        "",
        "═══ RINGKASAN EKSEKUTIF ═══",
        "\n".join(f"• {a}" for a in alasan),
        "",
        "═══ TEMUAN KLAUSUL BERACUN ═══",
        "\n\n".join(pp_lines) if pp_lines else "Tidak ada temuan kritis.",
        "",
        "═══ MATRIKS KEPATUHAN ═══",
        "\n".join(matrix_lines) if matrix_lines else "Tidak ada data matriks.",
        "",
        "─────────────────────────────────────────────────────────",
        "Dokumen ini dibuat otomatis oleh BidSentry v3.0.",
        "Verifikasi manual wajib dilakukan sebelum pengambilan keputusan final.",
    ])

    return {
        "title":   f"BidSentry Audit Dossier - {package_name}",
        "content": body,
    }


def _build_calendar_params(audit_data: dict) -> dict:
    """Build the input dict for GOOGLECALENDAR_CREATE_EVENT (H+7, 09:00-10:00 WIB)."""
    package_name = audit_data.get("nama_paket", "Pengadaan Jasa Konsultansi Portal Satu Data")
    wib          = timezone(timedelta(hours=7))
    now          = datetime.now(tz=wib)
    event_date   = now + timedelta(days=7)
    start        = event_date.replace(hour=9,  minute=0,  second=0, microsecond=0)
    end          = event_date.replace(hour=10, minute=0,  second=0, microsecond=0)

    poison_pills = audit_data.get("temuan_klausul_beracun", [])
    pp_summary   = "; ".join(pp.get("pasal", "") for pp in poison_pills[:2])

    description = (
        f"Batas klarifikasi/sanggah Aanwijzing untuk paket: {package_name}.\n\n"
        f"Temuan klausul beracun yang wajib diangkat:\n"
        f"{pp_summary or 'Lihat laporan BidSentry untuk detail.'}\n\n"
        f"Dibuat otomatis oleh BidSentry v3.0."
    )

    return {
        "summary":     f"[BidSentry] Batas Klarifikasi Aanwijzing — {package_name}",
        "description": description,
        "start":       {"dateTime": start.isoformat(), "timeZone": "Asia/Jakarta"},
        "end":         {"dateTime": end.isoformat(),   "timeZone": "Asia/Jakarta"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email",  "minutes": 1440},   # 1 day before
                {"method": "popup",  "minutes": 60},     # 1 hour before
            ],
        },
    }


def _build_gmail_params(audit_data: dict) -> dict:
    """Build the input dict for GMAIL_CREATE_EMAIL_DRAFT."""
    package_name = audit_data.get("nama_paket", "Pengadaan Jasa Konsultansi Portal Satu Data")
    now_str      = datetime.now(tz=timezone(timedelta(hours=7))).strftime("%d %B %Y")
    poison_pills = audit_data.get("temuan_klausul_beracun", [])

    pp_paragraphs = []
    for i, pp in enumerate(poison_pills, 1):
        pp_paragraphs.append(
            f"{i}. {pp.get('pasal', 'Klausul tidak diketahui')}\n"
            f"   Jenis Risiko  : {pp.get('jenis_risiko', '-')}\n"
            f"   Pelanggaran   : {pp.get('pelanggaran_regulasi', '-')}\n"
            f"   Rekomendasi   : {pp.get('saran_mitigasi', '-')}"
        )

    body = (
        f"Kepada Yth.\n"
        f"Tim Legal & Pengadaan\n\n"
        f"Dengan hormat,\n\n"
        f"Bersama ini kami sampaikan instruksi verifikasi klausul kontrak untuk paket:\n"
        f"  {package_name}\n\n"
        f"Berdasarkan hasil audit BidSentry ({now_str}), ditemukan {len(poison_pills)} "
        f"klausul berpotensi merugikan yang wajib dimitigasi sebelum penandatanganan kontrak:\n\n"
        + "\n\n".join(pp_paragraphs)
        + "\n\n"
        f"Mohon segera dilakukan:\n"
        f"1. Verifikasi klausul denda (KLA-02) terhadap SSUK LKPP Bab X.\n"
        f"2. Konfirmasi status termin APBN-P (KLA-01) dengan Bendahara Daerah.\n"
        f"3. Siapkan sanggahan resmi paling lambat pada sesi Aanwijzing (H+7).\n\n"
        f"Laporan lengkap tersedia di Google Docs Dossier yang terlampir.\n\n"
        f"Hormat kami,\n"
        f"BidSentry Audit System v3.0\n"
        f"(Pesan otomatis — jangan balas langsung ke alamat ini)"
    )

    return {
        "to":      "legal@perusahaan.internal",
        "subject": f"[BidSentry] Instruksi Verifikasi Klausul — {package_name}",
        "body":    body,
    }


# ─── Main dispatcher ──────────────────────────────────────────────────────────

def dispatch_tender_workspace(audit_data: dict) -> dict:
    """
    Execute 3 Composio actions for the given audit data.

    Returns a structured JSON-serialisable dict with:
      - overall status (success / partial / simulated / error)
      - per-action results (doc_url, event_url, draft_url)
      - any error messages

    This function never raises — all exceptions are caught and returned
    as structured error payloads so the calling server stays alive.
    """
    api_key = _get_api_key()

    results: dict = {
        "status":    "unknown",
        "simulated": False,
        "actions":   {},
        "errors":    [],
    }

    # ── Guard: missing API key ─────────────────────────────────────────────
    if not api_key:
        results["status"]    = "simulated"
        results["simulated"] = True
        results["message"]   = (
            "COMPOSIO_API_KEY não configurada. "
            "Retornando payload de simulação. "
            "Defina COMPOSIO_API_KEY no arquivo .env para modo live."
        )
        results["actions"]["GOOGLEDOCS_CREATE_DOCUMENT"]  = _simulate_result("GOOGLEDOCS_CREATE_DOCUMENT",  audit_data)
        results["actions"]["GOOGLECALENDAR_CREATE_EVENT"] = _simulate_result("GOOGLECALENDAR_CREATE_EVENT", audit_data)
        results["actions"]["GMAIL_CREATE_EMAIL_DRAFT"]    = _simulate_result("GMAIL_CREATE_EMAIL_DRAFT",    audit_data)

        # Convenience top-level URLs for the frontend
        results["doc_url"]   = results["actions"]["GOOGLEDOCS_CREATE_DOCUMENT"]["data"].get("documentUrl")
        results["event_url"] = results["actions"]["GOOGLECALENDAR_CREATE_EVENT"]["data"].get("eventUrl")
        results["draft_url"] = results["actions"]["GMAIL_CREATE_EMAIL_DRAFT"]["data"].get("draftUrl")
        return results

    # ── Live: call Composio ────────────────────────────────────────────────
    action_plan = [
        ("GOOGLEDOCS_CREATE_DOCUMENT",  _build_docs_params(audit_data)),
        ("GOOGLECALENDAR_CREATE_EVENT", _build_calendar_params(audit_data)),
        ("GMAIL_CREATE_EMAIL_DRAFT",    _build_gmail_params(audit_data)),
    ]

    success_count = 0
    for action_name, params in action_plan:
        try:
            response = _post_composio(action_name, api_key, params)
            results["actions"][action_name] = {
                "success": True,
                "simulated": False,
                "data": response,
            }
            success_count += 1
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            err_msg = f"{action_name}: HTTP {exc.code} — {error_body[:300]}"
            results["errors"].append(err_msg)
            results["actions"][action_name] = {
                "success":   False,
                "simulated": True,
                "error":     err_msg,
                "data":      _simulate_result(action_name, audit_data)["data"],
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            err_msg = f"{action_name}: Connection error — {exc}"
            results["errors"].append(err_msg)
            results["actions"][action_name] = {
                "success":   False,
                "simulated": True,
                "error":     err_msg,
                "data":      _simulate_result(action_name, audit_data)["data"],
            }
        except Exception as exc:  # noqa: BLE001
            err_msg = f"{action_name}: Unexpected error — {exc}"
            results["errors"].append(err_msg)
            results["actions"][action_name] = {
                "success":   False,
                "simulated": True,
                "error":     err_msg,
                "data":      _simulate_result(action_name, audit_data)["data"],
            }

    # Determine overall status
    if success_count == len(action_plan):
        results["status"] = "success"
    elif success_count > 0:
        results["status"] = "partial"
    else:
        results["status"] = "error"

    # Convenience top-level URLs
    doc_data   = results["actions"].get("GOOGLEDOCS_CREATE_DOCUMENT",  {}).get("data", {})
    cal_data   = results["actions"].get("GOOGLECALENDAR_CREATE_EVENT", {}).get("data", {})
    gmail_data = results["actions"].get("GMAIL_CREATE_EMAIL_DRAFT",    {}).get("data", {})

    # Composio may nest under "response_data" or return directly — handle both
    results["doc_url"]   = (
        doc_data.get("documentUrl")
        or doc_data.get("response_data", {}).get("documentUrl")
    )
    results["event_url"] = (
        cal_data.get("eventUrl")
        or cal_data.get("htmlLink")
        or cal_data.get("response_data", {}).get("htmlLink")
    )
    results["draft_url"] = (
        gmail_data.get("draftUrl")
        or gmail_data.get("response_data", {}).get("id")
    )

    return results


# ─── Standalone smoke-test ────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = {
        "nama_paket":    "Pengadaan Jasa Konsultansi Portal Satu Data",
        "verdict":       "GO-WITH-CAUTION",
        "risk_score":    "TINGGI",
        "alasan_utama": [
            "ADENDUM OVERRIDE: Nilai ambang diturunkan ke Rp 600M.",
            "CREDENTIAL RISK: Sertifikat Team Leader kedaluwarsa.",
            "LEGAL HAZARD: Dua klausul melanggar Perpres 16/2018.",
        ],
        "temuan_klausul_beracun": [
            {
                "pasal":               "KLA-01 — Termin Pembayaran Bersyarat APBN-P",
                "jenis_risiko":        "Risiko Likuiditas & Keterlambatan Pembayaran Tak Terbatas",
                "pelanggaran_regulasi":"Perpres 16/2018 jo. 12/2021 Pasal 56 ayat (2)",
                "saran_mitigasi":      "Ajukan sanggahan resmi pada masa aanwijzing (longstop date 30 hari).",
            },
            {
                "pasal":               "KLA-02 — Denda Keterlambatan Tanpa Batas Atas",
                "jenis_risiko":        "Eksposur Finansial Tak Terbatas (0,2% per hari)",
                "pelanggaran_regulasi":"SSUK LKPP Standar (maks 5% nilai kontrak)",
                "saran_mitigasi":      "Tuntut klausul standar SSUK Bab X via addendum.",
            },
        ],
        "matriks_kepatuhan": [],
    }

    print("Running dispatch_tender_workspace (smoke test)...\n")
    result = dispatch_tender_workspace(sample)
    print(json.dumps(result, indent=2, ensure_ascii=False))
