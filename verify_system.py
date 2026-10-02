#!/usr/bin/env python3
"""
BidSentry — System Verification
=================================
Checks that all required local services are reachable before running the
full stack. Uses Python stdlib only — no third-party packages needed.

Services checked:
  1. Langflow Core Engine   — http://localhost:7860/
  2. BidSentry Bridge Server — http://localhost:8000/

Exit codes:
  0 — All services UP
  1 — One or more services unreachable

Usage:
    python verify_system.py
"""

import sys
import urllib.error
import urllib.request

# ─── Service definitions ──────────────────────────────────────────────────────

SERVICES = [
    {
        "name":    "Langflow Core Engine",
        "url":     "http://localhost:7860/",
        "timeout": 5,
    },
    {
        "name":    "BidSentry Bridge Server",
        "url":     "http://localhost:8000/",
        "timeout": 5,
    },
]

# ─── Colours (disabled automatically on Windows without ANSICON / WT) ─────────

_RESET  = "\033[0m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_BOLD   = "\033[1m"


def _c(colour: str, text: str) -> str:
    """Wrap text in ANSI colour codes."""
    return f"{colour}{text}{_RESET}"


# ─── HTTP probe ───────────────────────────────────────────────────────────────

def _probe(url: str, timeout: int) -> tuple[bool, str]:
    """
    Attempt a GET to *url*.  Returns (is_up, detail_message).
    Any HTTP response (even 4xx/5xx) counts as UP — the process is listening.
    Only connection-level errors (refused, timeout, DNS) count as DOWN.
    """
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        # Server replied — it's up, even if it returned an error code
        return True, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if "refused" in reason.lower():
            return False, "Connection refused - service not running"
        if "timed out" in reason.lower() or "time" in reason.lower():
            return False, "Connection timed out"
        return False, reason
    except TimeoutError:
        return False, "Connection timed out"
    except OSError as exc:
        return False, str(exc)


# ─── Main ─────────────────────────────────────────────────────────────────────

_SEP = "-" * 56


def main() -> int:
    print()
    print(_c(_BOLD, _SEP))
    print(_c(_BOLD, "  BidSentry -- System Verification"))
    print(_c(_BOLD, _SEP))

    all_up   = True
    results  = []

    for svc in SERVICES:
        is_up, detail = _probe(svc["url"], svc["timeout"])
        results.append((svc["name"], svc["url"], is_up, detail))
        status_str = _c(_GREEN, "  [UP]  ") if is_up else _c(_RED, "  [DOWN]")
        print(f"  {status_str}  {svc['name']:<30}  {_c(_YELLOW, svc['url'])}")
        if not is_up:
            print(f"             +-- {_c(_RED, detail)}")
            all_up = False

    print(_c(_BOLD, _SEP))

    if all_up:
        print(_c(_GREEN, "  All services are UP. BidSentry is ready.\n"))
        return 0
    else:
        down = [r[0] for r in results if not r[2]]
        print(_c(_RED, f"  {len(down)} service(s) unreachable: {', '.join(down)}"))
        print()
        print("  Start missing services and re-run:")
        for name, _, is_up, _ in results:
            if not is_up:
                if "Langflow" in name:
                    print(_c(_YELLOW, "    langflow run --host 0.0.0.0 --port 7860"))
                elif "Bridge" in name:
                    print(_c(_YELLOW, "    python server.py"))
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
