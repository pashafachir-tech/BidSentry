"""Pytest configuration and environment fixtures for BidSentry."""
from __future__ import annotations

import warnings

# Suppress known external runtime/transition warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=r"Using `httpx` with `starlette\.testclient` is deprecated.*")
warnings.filterwarnings("ignore", message=r"Setting per-request cookies=.*is being deprecated.*")
