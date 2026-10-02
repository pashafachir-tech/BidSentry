#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BidSentry -- Backend Bridge Server
====================================
Serves index.html, handles POST /api/dispatch and POST /api/audit locally,
and proxies everything else under /api/* to Langflow (default: localhost:7860).

Usage:
    python server.py [--port 8000] [--langflow http://localhost:7860]

Requirements: Python 3.9+, stdlib only.
"""

import argparse
import http.client
import http.server
import io
import json
import os
import re
import sys
import uuid
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Force UTF-8 on stdout/stderr immediately (Windows CP1252 workaround).
# This must run at import time so worker threads inherit it.
# ---------------------------------------------------------------------------
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PORT     = 8000
DEFAULT_LANGFLOW = "http://localhost:7860"
WORKSPACE_ROOT   = Path(__file__).parent.resolve()
AUDIT_LOG_PATH   = WORKSPACE_ROOT / "audit_log.jsonl"

# Routes handled locally (not proxied to Langflow)
LOCAL_API_ROUTES = {"/api/dispatch", "/api/audit"}

# Path prefixes that get proxied to Langflow
PROXY_PREFIXES = ("/api/", "/flows/", "/health")


# ---------------------------------------------------------------------------
# MIME map
# ---------------------------------------------------------------------------

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".htm":  "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".mjs":  "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg":  "image/svg+xml",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".ico":  "image/x-icon",
    ".woff": "font/woff",
    ".woff2":"font/woff2",
    ".ttf":  "font/ttf",
    ".txt":  "text/plain; charset=utf-8",
    ".md":   "text/markdown; charset=utf-8",
}

def _mime(suffix: str) -> str:
    return _MIME.get(suffix.lower(), "application/octet-stream")


# ---------------------------------------------------------------------------
# CORS helpers
# ---------------------------------------------------------------------------

_CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-api-key",
    "Access-Control-Max-Age":       "3600",
}


# ---------------------------------------------------------------------------
# PII masking
# ---------------------------------------------------------------------------

_PII_RE = [
    (re.compile(r"\b\d{2}\.\d{3}\.\d{3}\.\d[-]\d{3}\.\d{3}\b"), "[NPWP-REDACTED]"),
    (re.compile(r"\b\d{16}\b"),  "[NIK-REDACTED]"),
    (re.compile(r"\b\d{10,15}\b"), "[REKENING-REDACTED]"),
]

def _mask_str(text: str) -> str:
    for pat, rep in _PII_RE:
        text = pat.sub(rep, text)
    return text

def _mask_any(obj: Any) -> Any:
    if isinstance(obj, str):
        return _mask_str(obj)
    if isinstance(obj, dict):
        return {k: _mask_any(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mask_any(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def _log_audit(event_id: str, payload: Any, verdict: str, mode: str) -> None:
    entry = {
        "ts":      datetime.now(tz=timezone.utc).isoformat(),
        "id":      event_id,
        "payload": payload,
        "verdict": verdict,
        "mode":    mode,
    }
    try:
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[AUDIT LOG ERROR] {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Rules engine (mirrors parseDocumentToMatrix in index.html)
# ---------------------------------------------------------------------------

_RULES = [
    ("KL-001", "Klasifikasi Usaha (SBU/KBLI)",              "Kualifikasi",
     [r"\bSBU\b", r"\bKBLI\b", r"klasifikasi usaha"]),
    ("KL-002", "Pengalaman Sejenis",                         "Kualifikasi",
     [r"pengalaman sejenis", r"nilai kontrak", r"kontrak sejenis"]),
    ("KL-003", "NPWP & Status Perpajakan",                   "Kualifikasi",
     [r"\bNPWP\b", r"\bPKP\b", r"status pajak"]),
    ("KL-004", "SPT Tahunan",                                "Administrasi",
     [r"\bSPT\b", r"pajak penghasilan", r"PPh Badan"]),
    ("TEK-001", "Personel Teknis (Pendidikan & SKK)",        "Teknis",
     [r"\bSKK\b", r"team leader", r"personel teknis", r"ahli muda"]),
    ("TEK-002", "Peralatan / Infrastruktur",                 "Teknis",
     [r"peralatan", r"\bserver\b", r"infrastruktur", r"hosting"]),
    ("KO-001",  "Sanksi Keterlambatan / Liquidated Damages", "Kontrak",
     [r"sanksi keterlambatan", r"\bdenda\b", r"1/1000",
      r"liquidated damages", r"keterlambatan"]),
    ("KO-002",  "Termin Pembayaran",                         "Kontrak",
     [r"termin pembayaran", r"pembayaran", r"\bBAST\b", r"serah terima"]),
    ("KO-003",  "Force Majeure",                             "Kontrak",
     [r"force majeure", r"keadaan kahar", r"KUHPerdata"]),
]

def _hit(text: str, patterns: list) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def run_rules_engine(dok: str, adendum: str, pustaka: str) -> dict:
    dok_m   = _mask_str(dok)
    aden_m  = _mask_str(adendum)
    pust_m  = _mask_str(pustaka)
    combo   = dok_m + "\n" + aden_m

    rows = []
    for rid, label, kat, pats in _RULES:
        if not _hit(combo, pats):
            continue

        in_pustaka = _hit(pust_m, pats)
        in_adendum = bool(aden_m) and _hit(aden_m, pats)

        if in_pustaka:
            status = "TERPENUHI"
        elif in_adendum:
            status = "SUPERSEDED"
        else:
            status = "GAP"

        if status == "TERPENUHI" and _hit(pust_m, [r"expir", r"akan berakhir", r"mendekati"]):
            status = "EXPIRING"

        snippet = label
        for line in dok_m.splitlines():
            if _hit(line, pats):
                snippet = line.strip()[:120]
                break

        rows.append({
            "id":            rid,
            "kategori":      kat,
            "klausul_resmi": snippet,
            "status":        status,
            "catatan":       "BidSentry Rules Engine v1.0 - " + (
                "Adendum aktif" if in_adendum else "Tidak ada adendum"),
        })

    gap      = sum(1 for r in rows if r["status"] == "GAP")
    expiring = sum(1 for r in rows if r["status"] == "EXPIRING")
    lolos    = sum(1 for r in rows if r["status"] == "TERPENUHI")

    if gap == 0 and expiring == 0:
        verdict    = "CLEAN GO"
        risk_score = "RENDAH"
    elif gap >= 2:
        verdict    = "NO-GO MUTLAK"
        risk_score = "TINGGI"
    else:
        verdict    = "GO-WITH-CAUTION"
        risk_score = "SEDANG"

    return {
        "verdict":    verdict,
        "risk_score": risk_score,
        "summary":    {"total": len(rows), "lolos": lolos, "gap": gap, "expiring": expiring},
        "matriks":    rows,
        "engine":     "BidSentry Rules Engine v1.0 (server-side)",
    }


# ---------------------------------------------------------------------------
# Langflow URL parser
# ---------------------------------------------------------------------------

def _parse_langflow_url(raw: str):
    p    = urllib.parse.urlparse(raw)
    host = p.hostname or "localhost"
    port = p.port or (443 if p.scheme == "https" else 80)
    return host, port, p.scheme


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class BridgeHandler(http.server.BaseHTTPRequestHandler):

    # Class-level attributes filled by build_handler()
    langflow_host:   str = "localhost"
    langflow_port:   int = 7860
    langflow_scheme: str = "http"

    # ------------------------------------------------------------------
    # Logging: suppress successful GET noise, keep errors
    # ------------------------------------------------------------------
    def log_message(self, format, *args):  # noqa: A002
        # Only print 4xx / 5xx responses
        if args and len(args) >= 2 and str(args[1]).startswith(("4", "5")):
            sys.stderr.write(
                "%s - - [%s] %s\n" % (
                    self.address_string(),
                    self.log_date_time_string(),
                    format % args,
                )
            )
            sys.stderr.flush()

    def log_request(self, code="-", size="-"):
        method = getattr(self, "command", "???") or "???"
        path   = getattr(self, "path",    "/")   or "/"
        try:
            sys.stdout.write("  %-7s %s  [%s]\n" % (method, path, code))
            sys.stdout.flush()
        except Exception:
            pass  # never let logging crash the handler

    # ------------------------------------------------------------------
    # CORS preflight
    # ------------------------------------------------------------------
    def do_OPTIONS(self):
        self._send_cors_preflight()

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def do_GET(self):
        try:
            if self._is_proxy():
                self._proxy("GET", None)
            else:
                self._serve_static()
        except Exception as exc:
            self._json_error(500, "Internal server error: " + str(exc))

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
    def do_POST(self):
        try:
            path = urllib.parse.urlparse(self.path).path
            if path in LOCAL_API_ROUTES:
                if path == "/api/dispatch":
                    self._handle_dispatch()
                else:
                    self._handle_audit()
            elif self._is_proxy():
                length = int(self.headers.get("Content-Length", 0))
                body   = self.rfile.read(length) if length > 0 else b""
                self._proxy("POST", body)
            else:
                self._json_error(404, "Not found")
        except Exception as exc:
            self._json_error(500, "Internal server error: " + str(exc))

    # ------------------------------------------------------------------
    # PUT / PATCH / DELETE
    # ------------------------------------------------------------------
    def do_PUT(self):    self._proxy_or_404("PUT")
    def do_PATCH(self):  self._proxy_or_404("PATCH")
    def do_DELETE(self): self._proxy_or_404("DELETE")

    def _proxy_or_404(self, method: str):
        try:
            if self._is_proxy():
                length = int(self.headers.get("Content-Length", 0))
                body   = self.rfile.read(length) if length > 0 else None
                self._proxy(method, body)
            else:
                self._json_error(404, "Not found")
        except Exception as exc:
            self._json_error(500, "Internal server error: " + str(exc))

    # ------------------------------------------------------------------
    # /api/dispatch  -- forward to composio_dispatcher
    # ------------------------------------------------------------------
    def _handle_dispatch(self):
        length   = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._json_error(400, "Invalid JSON: " + str(exc))
            return
        if not isinstance(parsed, dict):
            self._json_error(400, "Request body must be a JSON object.")
            return

        masked: dict = _mask_any(parsed)

        try:
            from composio_dispatcher import dispatch_tender_workspace
            result: dict = dispatch_tender_workspace(masked)
        except ImportError:
            result = {"ok": False, "simulated": True,
                      "message": "composio_dispatcher not available; running in demo mode."}

        eid     = str(uuid.uuid4())
        verdict = masked.get("verdict", "UNKNOWN")
        mode    = "SIMULATED" if result.get("simulated") else "LIVE"
        _log_audit(eid, masked, verdict, mode)
        print("  DISPATCH /api/dispatch -> composio [%s]" % eid[:8])

        self._json_ok(result)

    # ------------------------------------------------------------------
    # /api/audit  -- server-side rules engine
    # ------------------------------------------------------------------
    def _handle_audit(self):
        length   = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._json_error(400, "Invalid JSON: " + str(exc))
            return
        if not isinstance(parsed, dict):
            self._json_error(400, "Request body must be a JSON object.")
            return

        dok     = str(parsed.get("dok_pemilihan", "")).strip()
        adendum = str(parsed.get("adendum",       "")).strip()
        pustaka = str(parsed.get("pustaka",        "")).strip()

        if not dok and not adendum and not pustaka:
            self._json_error(400, "Provide at least one of: dok_pemilihan, adendum, pustaka.")
            return

        result = run_rules_engine(dok, adendum, pustaka)
        eid    = str(uuid.uuid4())
        _log_audit(eid, {"dok_len": len(dok), "adendum_len": len(adendum),
                         "pustaka_len": len(pustaka)},
                   result["verdict"], "LOCAL_ENGINE")
        print("  AUDIT    /api/audit  verdict=%s [%s]" % (result["verdict"], eid[:8]))

        self._json_ok(result)

    # ------------------------------------------------------------------
    # Static file serving
    # ------------------------------------------------------------------
    def _serve_static(self):
        url_path = urllib.parse.urlparse(self.path).path
        if url_path in ("/", ""):
            url_path = "/index.html"

        file_path = (WORKSPACE_ROOT / url_path.lstrip("/")).resolve()

        # Directory traversal guard
        try:
            file_path.relative_to(WORKSPACE_ROOT)
        except ValueError:
            self._json_error(403, "Forbidden")
            return

        if not file_path.exists() or file_path.is_dir():
            self._json_error(404, "Not found: " + url_path)
            return

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _mime(file_path.suffix))
        self.send_header("Content-Length", str(len(data)))
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    # ------------------------------------------------------------------
    # Langflow proxy
    # ------------------------------------------------------------------
    def _proxy(self, method: str, body):
        fwd = {}
        for h in ("Content-Type", "Authorization", "x-api-key", "Accept"):
            v = self.headers.get(h)
            if v:
                fwd[h] = v
        if body:
            fwd["Content-Length"] = str(len(body))

        try:
            if self.langflow_scheme == "https":
                conn = http.client.HTTPSConnection(
                    self.langflow_host, self.langflow_port, timeout=120)
            else:
                conn = http.client.HTTPConnection(
                    self.langflow_host, self.langflow_port, timeout=120)

            conn.request(method, self.path, body=body, headers=fwd)
            resp = conn.getresponse()

            self.send_response(resp.status)
            for k, v in _CORS.items():
                self.send_header(k, v)
            hop = {"transfer-encoding","connection","keep-alive","proxy-authenticate",
                   "proxy-authorization","te","trailers","upgrade"}
            for hdr, val in resp.getheaders():
                if hdr.lower() not in hop:
                    self.send_header(hdr, val)
            self.end_headers()

            is_sse = "text/event-stream" in resp.getheader("Content-Type", "")
            if is_sse:
                try:
                    while True:
                        chunk = resp.read(1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.wfile.write(resp.read())

            conn.close()

        except ConnectionRefusedError:
            self._json_error(502,
                "Langflow is not running at %s://%s:%s. "
                "Start it with: langflow run --port 7860" % (
                    self.langflow_scheme, self.langflow_host, self.langflow_port))
        except TimeoutError:
            self._json_error(504, "Upstream timeout from Langflow.")
        except Exception as exc:
            self._json_error(500, "Proxy error: " + str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_proxy(self) -> bool:
        path = urllib.parse.urlparse(self.path).path
        return any(path.startswith(p) for p in PROXY_PREFIXES)

    def _send_cors_preflight(self):
        self.send_response(204)
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def _json_ok(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, code: int, msg: str):
        body = json.dumps({"error": msg}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------

def build_handler(langflow_url: str):
    host, port, scheme = _parse_langflow_url(langflow_url)

    class _H(BridgeHandler):
        langflow_host   = host
        langflow_port   = port
        langflow_scheme = scheme

    return _H


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run(port: int = DEFAULT_PORT, langflow_url: str = DEFAULT_LANGFLOW):
    handler = build_handler(langflow_url)
    httpd   = http.server.ThreadingHTTPServer(("", port), handler)

    print("------------------------------------------------------------")
    print("  BidSentry Bridge Server  v3.0")
    print("------------------------------------------------------------")
    print("  Frontend  ->  http://localhost:%d" % port)
    print("  Langflow  ->  %s" % langflow_url)
    print("  Workspace ->  %s" % WORKSPACE_ROOT)
    print("------------------------------------------------------------")
    print("  Ctrl+C to stop.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        httpd.shutdown()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="BidSentry bridge server -- serves frontend, proxies to Langflow."
    )
    parser.add_argument("--port", "-p", type=int,
                        default=int(os.environ.get("BRIDGE_PORT", DEFAULT_PORT)),
                        help="Port to listen on (default: %d)" % DEFAULT_PORT)
    parser.add_argument("--langflow", "-l", type=str,
                        default=os.environ.get("LANGFLOW_HOST", DEFAULT_LANGFLOW),
                        help="Langflow base URL (default: %s)" % DEFAULT_LANGFLOW)
    args = parser.parse_args()
    run(port=args.port, langflow_url=args.langflow)


if __name__ == "__main__":
    main()
