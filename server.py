#!/usr/bin/env python3
"""BidSentry local application entry point.

The HTTP transport, routes, controllers, and business services live in the
``bidsentry`` package. This file is intentionally kept as a small CLI wrapper
for compatibility with ``python server.py`` and the existing launcher.
"""

from __future__ import annotations

import argparse
from dataclasses import replace

from bidsentry.config import Settings
from bidsentry.asgi import create_asgi_app
from bidsentry.services.audit_service import AuditService
from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest
from bidsentry.types.schemas import AuditRequest


def run(port: int | None = None, langflow_url: str | None = None) -> None:
    import uvicorn

    settings = Settings.from_environment()
    if port is not None:
        settings = replace(settings, port=port)
    if langflow_url is not None:
        settings = replace(settings, langflow_url=langflow_url.rstrip("/"))
    uvicorn.run(create_asgi_app(settings), host=settings.host, port=settings.port, access_log=False)


def run_rules_engine(dok: str, adendum: str, pustaka: str) -> dict:
    """Compatibility adapter for scripts that imported the former helper."""
    request = AuditRequest("Audit dokumen", dok, adendum, pustaka)
    return AuditService().audit(request)


def create_evaluation_client(settings: Settings | None = None) -> EvaluationEngine:
    """Create the shared evaluator; Langflow is preferred when configured and consented."""
    return EvaluationEngine(settings or Settings.from_environment())


def evaluate_tender(payload: dict, settings: Settings | None = None) -> dict:
    """Synchronous fallback client for scripts and the local API transport."""
    request = EvaluationRequest.model_validate(payload)
    return create_evaluation_client(settings).evaluate(request)


def main() -> None:
    settings = Settings.from_environment()
    parser = argparse.ArgumentParser(description="Start the BidSentry local review workspace.")
    parser.add_argument("--port", "-p", type=int, default=settings.port, help="HTTP port")
    parser.add_argument("--langflow", "-l", default=settings.langflow_url, help="Langflow base URL")
    args = parser.parse_args()
    run(port=args.port, langflow_url=args.langflow)


if __name__ == "__main__":
    main()
