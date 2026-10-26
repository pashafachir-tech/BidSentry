#!/usr/bin/env python3
"""
BidSentry — Composio Dispatcher
=================================
Prepares 3 workspace follow-up artifacts through the Composio REST API:

  1. GOOGLEDOCS_CREATE_DOCUMENT  — Review summary for human verification
  2. GOOGLECALENDAR_CREATE_EVENT — Provisional internal reminder (H+7)
  3. GMAIL_CREATE_EMAIL_DRAFT    — Unaddressed internal review draft

All I/O uses Python stdlib only (urllib.request, json, os, datetime).
No third-party pip dependencies are required.

Environment:
    COMPOSIO_API_KEY  — Composio API key (required for live mode)
                        Falls back to reading .env file if not set in env.

"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from bidsentry.config import Settings, load_env_file


# ─── Configuration ────────────────────────────────────────────────────────────

load_env_file()


def _get_api_key() -> str | None:
    """Return the Composio API key from the centralized environment config."""
    return os.environ.get("COMPOSIO_API_KEY", "").strip() or None


# ─── Low-level HTTP helper ────────────────────────────────────────────────────

def _post_composio(action: str, api_key: str, params: dict) -> dict:
    """
    POST to the Composio execute endpoint for *action*.
    Returns the parsed JSON response dict.
    Raises urllib.error.URLError / urllib.error.HTTPError on network failure.
    """
    settings = Settings.from_environment()
    url     = settings.composio_base_url.format(action=action)
    payload = json.dumps({
        "entityId":    settings.composio_entity_id,
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
    with urllib.request.urlopen(req, timeout=settings.composio_timeout_seconds) as resp:
        response_body = resp.read(2 * 1024 * 1024 + 1)
    if len(response_body) > 2 * 1024 * 1024:
        raise ValueError("Composio response exceeds the 2 MB limit.")
    response_data = json.loads(response_body.decode("utf-8"))
    if not isinstance(response_data, dict):
        raise ValueError("Composio returned an invalid response object.")
    return response_data


# ─── Action builders ──────────────────────────────────────────────────────────

def _build_docs_params(audit_data: dict) -> dict:
    """Build the input dict for GOOGLEDOCS_CREATE_DOCUMENT."""
    package_name   = audit_data.get("nama_paket", "Audit pengadaan")
    verdict        = audit_data.get("verdict", "GO-WITH-CAUTION")
    risk_score     = audit_data.get("risk_score", "—")
    alasan         = audit_data.get("alasan_utama", [])
    now_str        = datetime.now(tz=timezone(timedelta(hours=7))).strftime("%d %B %Y %H:%M WIB")

    body = "\n\n".join([
        f"BIDSENTRY AUDIT DOSSIER",
        f"Paket   : {package_name}",
        f"ID      : {audit_data.get('tender_id') or '—'}",
        f"Dibuat  : {now_str}",
        f"Status review : {verdict}",
        f"Indeks triase : {risk_score}/100",
        "",
        "═══ SINYAL UNTUK VERIFIKASI MANUAL ═══",
        "\n".join(f"• {a}" for a in alasan),
        "",
        "Ketiadaan sinyal bukan bukti kepatuhan; periksa dokumen dan bukti sumber.",
        "",
        "─────────────────────────────────────────────────────────",
        "Dibuat sebagai ringkasan review. Indeks triase bukan verdict hukum, kepatuhan, atau fraud.",
        "Reviewer wajib memeriksa dokumen asli sebelum tindak lanjut atau keputusan.",
    ])

    return {
        "title":   f"BidSentry Audit Dossier - {package_name}",
        "content": body,
    }


def _build_calendar_params(audit_data: dict) -> dict:
    """Build a provisional internal reminder (H+7, 09:00–09:30 WIB)."""
    package_name = audit_data.get("nama_paket", "Audit pengadaan")
    wib = timezone(timedelta(hours=7))
    now = datetime.now(tz=wib)
    event_date = now + timedelta(days=7)
    start = event_date.replace(hour=9, minute=0, second=0, microsecond=0)
    end = event_date.replace(hour=9, minute=30, second=0, microsecond=0)
    reasons = audit_data.get("alasan_utama", [])
    reason_summary = "; ".join(reasons[:2]) if reasons else "Belum ada ringkasan sinyal; periksa review di BidSentry."

    description = (
        f"Pengingat internal untuk meninjau paket: {package_name}.\n"
        f"Sinyal untuk diverifikasi: {reason_summary}\n\n"
        "Waktu H+7 ini adalah pengingat default, bukan tenggat resmi tender. "
        "Periksa dan ubah tanggal berdasarkan jadwal resmi sebelum mengandalkannya."
    )
    return {
        "summary": f"[BidSentry] Pengingat review internal — {package_name}",
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Jakarta"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Jakarta"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 1440},
                {"method": "popup", "minutes": 60},
            ],
        },
    }

def _build_gmail_params(audit_data: dict) -> dict:
    """Build an internal review draft; it never sends an email."""
    package_name = audit_data.get("nama_paket", "Audit pengadaan")
    now_str = datetime.now(tz=timezone(timedelta(hours=7))).strftime("%d %B %Y")
    reasons = audit_data.get("alasan_utama", [])
    reason_lines = "\n".join(f"{i}. {reason}" for i, reason in enumerate(reasons, 1))
    body = (
        "Dengan hormat,\n\n"
        f"Mohon dilakukan peninjauan internal atas paket: {package_name}.\n"
        f"Ringkasan sinyal BidSentry ({now_str}) untuk diverifikasi terhadap dokumen sumber:\n\n"
        + (reason_lines or "Belum ada sinyal yang ditampilkan. Periksa dokumen sumber secara menyeluruh.")
        + "\n\nCatatan: indeks triase dan sinyal aturan bukan kesimpulan hukum, kepatuhan, atau fraud. "
        "Cocokkan setiap poin dengan dokumen dan versi yang berlaku sebelum mengambil tindakan.\n\n"
        "Hormat kami,\n[Nama dan jabatan]"
    )
    return {
        "to": audit_data.get("email_penerima", ""),
        "subject": f"[Draf BidSentry] Review internal — {package_name}",
        "body": body,
    }


# ─── Main dispatcher ──────────────────────────────────────────────────────────

def dispatch_tender_workspace(audit_data: dict) -> dict:
    """
    Execute 3 Composio actions for the given audit data.

    Returns a structured JSON-serialisable dict with actual connector status.

    This function never raises — all exceptions are caught and returned
    as structured error payloads so the calling server stays alive.
    """
    api_key = _get_api_key()
    action_plan = [
        ("GOOGLEDOCS_CREATE_DOCUMENT", _build_docs_params(audit_data)),
        ("GOOGLECALENDAR_CREATE_EVENT", _build_calendar_params(audit_data)),
    ]
    if audit_data.get("email_penerima"):
        action_plan.append(("GMAIL_CREATE_EMAIL_DRAFT", _build_gmail_params(audit_data)))

    results: dict = {
        "status":    "unknown",
        "actions":   {},
        "errors":    [],
    }

    # ── Guard: missing API key ─────────────────────────────────────────────
    if not api_key:
        results["status"] = "unavailable"
        results["message"] = "COMPOSIO_API_KEY belum dikonfigurasi; tidak ada tindakan yang dijalankan."
        return results

    # ── Live: call Composio ────────────────────────────────────────────────
    success_count = 0
    for action_name, params in action_plan:
        try:
            response = _post_composio(action_name, api_key, params)
            results["actions"][action_name] = {
                "success": True,
                "data": response,
            }
            success_count += 1
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            err_msg = f"{action_name}: HTTP {exc.code} — {error_body[:300]}"
            results["errors"].append(err_msg)
            results["actions"][action_name] = {
                "success":   False,
                "error":     err_msg,
                "data":      {},
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            err_msg = f"{action_name}: Connection error — {exc}"
            results["errors"].append(err_msg)
            results["actions"][action_name] = {
                "success":   False,
                "error":     err_msg,
                "data":      {},
            }
        except Exception as exc:  # noqa: BLE001
            err_msg = f"{action_name}: Unexpected error — {exc}"
            results["errors"].append(err_msg)
            results["actions"][action_name] = {
                "success":   False,
                "error":     err_msg,
                "data":      {},
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
