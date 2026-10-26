"""Compatibility facade for the unified procurement evaluation engine."""

from __future__ import annotations

from typing import Any

from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest
from bidsentry.types.schemas import AuditRequest


class AuditService:
    def __init__(self, engine: EvaluationEngine | None = None):
        self.engine = engine or EvaluationEngine()

    def audit(self, request: EvaluationRequest | AuditRequest | dict[str, Any]) -> dict[str, Any]:
        if isinstance(request, AuditRequest):
            model = EvaluationRequest(
                package_name=request.package_name,
                dok_pemilihan=request.dok_pemilihan,
                adendum=request.adendum,
                pustaka=request.pustaka,
                allow_external_processing=request.allow_external_processing,
                review_role=request.review_role,
            )
        elif isinstance(request, EvaluationRequest):
            model = request
        else:
            model = EvaluationRequest.model_validate(request)
        return self.engine.evaluate(model)
