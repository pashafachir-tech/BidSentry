"""Demo-grade role login for the two BidSentry personas: Pokja and Vendor.

A user chooses a role and (when configured) enters that role's PIN. The server
issues an HMAC-signed, HttpOnly session cookie that carries only the role and an
expiry. Every role-specific endpoint checks this cookie server-side, so the
Pokja and Vendor flows are separated in the backend, not just in the UI.

PINs come from ``BIDSENTRY_POKJA_PIN`` / ``BIDSENTRY_VENDOR_PIN``. When a PIN is
unset the role can log in without one **only** while the server listens on a
loopback host (local demo). This is not a substitute for an identity provider.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from enum import Enum
from typing import Any

from bidsentry.config import Settings

SESSION_COOKIE = "bidsentry_session"
SESSION_TTL_SECONDS = 8 * 3600
_PROCESS_SECRET = secrets.token_bytes(32)


class Role(str, Enum):
    POKJA = "pokja"
    VENDOR = "vendor"

    @property
    def label(self) -> str:
        return {"pokja": "Pokja Pemilihan", "vendor": "Penyedia / Vendor"}[self.value]

    @property
    def capabilities(self) -> list[str]:
        return {
            "pokja": ["audit.create", "audit.read", "document.berita_acara", "document.klarifikasi", "export.boq", "export.review"],
            "vendor": ["audit.create", "audit.read", "document.sanggahan", "export.boq", "export.review"],
        }[self.value]


class AuthError(Exception):
    def __init__(self, code: str, message: str, status: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _secret(settings: Settings) -> bytes:
    configured = getattr(settings, "session_secret", "") or ""
    return configured.encode("utf-8") if configured else _PROCESS_SECRET


def _pin_for(role: Role, settings: Settings) -> str:
    return (settings.pokja_pin if role is Role.POKJA else settings.vendor_pin) or ""


def _is_loopback(host: str) -> bool:
    return host.strip().casefold() in {"127.0.0.1", "localhost", "::1"}


def pin_required(role: Role, settings: Settings) -> bool:
    return bool(_pin_for(role, settings)) or not _is_loopback(settings.host)


def login(role_value: Any, pin: Any, settings: Settings) -> str:
    """Validate credentials and return a signed session token."""
    try:
        role = Role(str(role_value or "").strip().casefold())
    except ValueError as exc:
        raise AuthError("INVALID_ROLE", "Pilih peran Pokja atau Vendor.", 400) from exc
    expected = _pin_for(role, settings)
    if expected:
        if not isinstance(pin, str) or not hmac.compare_digest(pin.strip(), expected):
            raise AuthError("INVALID_PIN", "PIN tidak sesuai untuk peran ini.", 401)
    elif not _is_loopback(settings.host):
        raise AuthError("ROLE_DISABLED", f"PIN {role.label} belum dikonfigurasi pada server non-lokal.", 403)
    return issue_token(role, settings)


def issue_token(role: Role, settings: Settings, now: float | None = None) -> str:
    payload = {"role": role.value, "exp": int((now if now is not None else time.time()) + SESSION_TTL_SECONDS), "nonce": secrets.token_hex(8)}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    signature = hmac.new(_secret(settings), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def role_from_token(token: str | None, settings: Settings, now: float | None = None) -> Role | None:
    if not token or "." not in token:
        return None
    body, signature = token.rsplit(".", 1)
    expected = hmac.new(_secret(settings), body.encode("ascii", "ignore"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if int(payload.get("exp", 0)) < (now if now is not None else time.time()):
            return None
        return Role(payload.get("role"))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def require_role(role: Role | str | None, *allowed: Role) -> Role:
    """Raise 401 when not logged in, 403 when logged in with the wrong role."""
    if role is None or role == "":
        raise AuthError("LOGIN_REQUIRED", "Masuk sebagai Pokja atau Vendor terlebih dahulu.", 401)
    resolved = Role(role) if not isinstance(role, Role) else role
    if resolved not in allowed:
        names = " atau ".join(item.label for item in allowed)
        raise AuthError("ROLE_FORBIDDEN", f"Fitur ini hanya untuk {names}. Anda masuk sebagai {resolved.label}.", 403)
    return resolved


def describe(role: Role | None, settings: Settings) -> dict[str, Any]:
    return {
        "authenticated": role is not None,
        "role": role.value if role else None,
        "label": role.label if role else None,
        "capabilities": role.capabilities if role else [],
        "roles": [
            {"role": item.value, "label": item.label, "pin_required": pin_required(item, settings)}
            for item in Role
        ],
    }


__all__ = ["AuthError", "Role", "SESSION_COOKIE", "describe", "issue_token", "login", "require_role", "role_from_token"]
