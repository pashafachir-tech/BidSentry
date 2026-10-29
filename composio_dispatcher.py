#!/usr/bin/env python3
"""Root compatibility shim for composio_dispatcher.

The canonical implementation is located at bidsentry.services.composio_dispatcher per
docs/ARCHITECTURE_CONSOLIDATED.md.
"""
from __future__ import annotations

from typing import Any
import bidsentry.services.composio_dispatcher as _svc
from bidsentry.services.composio_dispatcher import *  # noqa: F401, F403
from bidsentry.services.composio_dispatcher import (  # noqa: F401
    _build_calendar_params,
    _build_docs_params,
    _build_gmail_params,
    _get_api_key,
    _post_composio,
    test_composio_connection,
    urllib,
)


def dispatch_tender_workspace(audit_data: dict, settings: Any = None) -> dict:
    """Delegate to bidsentry.services.composio_dispatcher while respecting monkeypatches."""
    curr_post = globals().get("_post_composio", _svc._post_composio)
    orig_post = _svc._post_composio
    _svc._post_composio = curr_post
    try:
        return _svc.dispatch_tender_workspace(audit_data, settings=settings)
    finally:
        _svc._post_composio = orig_post
