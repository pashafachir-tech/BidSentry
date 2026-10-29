"""Backward-compatibility re-export shim for the unified procurement evaluation engine."""

from __future__ import annotations

from typing import Any

from bidsentry.config import Settings
from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest
from bidsentry.schemas.comprehensive import ComprehensiveAuditRequest
from bidsentry.services.comprehensive_audit_service import (
    ComprehensiveAuditInputError,
    ComprehensiveAuditService,
)
from bidsentry.services.langflow_service import LangflowService
from bidsentry.types.schemas import AuditRequest


class AuditService:
    def __init__(
        self,
        engine: EvaluationEngine | None = None,
        comprehensive: ComprehensiveAuditService | None = None,
    ):
        self.engine = engine or EvaluationEngine()
        self.comprehensive = comprehensive

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

    def audit_comprehensive(
        self,
        request: ComprehensiveAuditRequest,
        audit_run_id: str | None = None,
        settings: Settings | None = None,
        langflow: LangflowService | None = None,
    ) -> dict[str, Any]:
        """Execute the comprehensive 10-module enterprise procurement audit."""
        svc = self.comprehensive or ComprehensiveAuditService(
            settings or Settings.from_environment(), langflow
        )
        return svc.audit(request, audit_run_id=audit_run_id)


__all__ = ["AuditService", "ComprehensiveAuditInputError", "ComprehensiveAuditService"]
