"""Audit and portfolio controllers."""

from __future__ import annotations

from typing import Any

from bidsentry.lib.audit_log import AuditLog
from bidsentry.services.audit_service import AuditService
from bidsentry.services.langflow_service import LangflowService
from bidsentry.services.portfolio_service import PortfolioService
from bidsentry.evaluators.engine import EvaluationRequest
from bidsentry.types.schemas import ValidationError


class AuditController:
    def __init__(self, audit_service: AuditService, langflow: LangflowService, audit_log: AuditLog, watsonx: Any = None):
        self.audit_service = audit_service
        self.langflow = langflow
        self.audit_log = audit_log
        self.watsonx = watsonx

    def create(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request body harus berupa objek JSON.", [{"field": "$", "issue": "expected_object"}])
        try:
            request = EvaluationRequest.model_validate(payload)
        except Exception as exc:
            from pydantic import ValidationError as PydanticValidationError
            if not isinstance(exc, PydanticValidationError):
                raise
            details = [{"field": ".".join(str(part) for part in item["loc"]), "issue": str(item["type"]), "message": str(item["msg"])} for item in exc.errors(include_url=False)]
            raise ValidationError("Request evaluasi tidak memenuhi skema.", details) from exc
        if not request.all_document_text:
            raise ValidationError("Masukkan setidaknya satu teks dokumen.", [{"field": "dok_pemilihan", "issue": "at_least_one_document_required"}])
        result = self.audit_service.audit(request)
        contextual = result.get("contextual_extraction", {})
        integration = {
            "status": contextual.get("status", "not_requested"),
            "advisory": None,
            "review_role": request.review_role,
            "message": contextual.get("message"),
            "provider": contextual.get("provider"),
        }
        result["integrations"] = {"langflow": integration}
        result["has_source_text"] = bool(request.all_document_text)

        from bidsentry.lib.pii import count_redacted_pii

        pii_tokens = count_redacted_pii(request.all_document_text)
        watsonx_status = self.watsonx.status() if hasattr(self, "watsonx") and self.watsonx else {"configured": False, "model_id": "ibm/granite-3-8b-instruct"}
        langflow_status = self.langflow.status() if hasattr(self, "langflow") and self.langflow else {"configured": False}

        ai_governance = {
            "foundation_model": watsonx_status.get("model_id") or "ibm/granite-3-8b-instruct",
            "provider": "ibm_watsonx_ai",
            "watsonx_connected": watsonx_status.get("configured", False),
            "mode": "enterprise_granite" if watsonx_status.get("configured") else "local_guardrail_active",
            "pii_governance": {
                "policy": "UU_27_2022_PDP",
                "status": "RULE_BASED_REDACTION",
                "redacted_token_count": pii_tokens,
                "scope": "pola NIK, NPWP, nomor rekening, telepon, dan email (tidak menyensor nama/alamat)",
                "deterministic_sanitization": True,
            },
            "guardrails": {
                "hallucination_prevention": "EXACT_SUBSTRING_LEXICAL_MATCHING",
                "drift_monitoring": "NOT_IMPLEMENTED",
                "statutory_alignment": "PERPRES_12_2021",
            },
            "orchestration": {
                "langflow_ready": langflow_status.get("configured", False),
                "flow_definition": "tender_extraction_flow.json",
            },
        }
        result["ai_governance_metadata"] = ai_governance

        if request.all_document_text:
            self.audit_log.save_source_text(
                result["audit_id"],
                request.all_document_text,
            )
        self.audit_log.append({
            "event_type": "audit.completed",
            "audit_id": result["audit_id"],
            "review_role": request.review_role,
            "package_name": request.package_name,
            "tender_id": request.tender_id,
            "notice_number": request.notice_number,
            "pokja_name": request.pokja_name,
            "company_name": request.company_name,
            "contract_value_idr": request.contract_value_idr,
            "verdict": result["verdict"],
            "risk": result["risk"],
            "summary": result["summary"],
            "engine_duration_ms": result.get("performance", {}).get("engine_duration_ms"),
            "findings": result["findings"],
            "executive_summary": result.get("executive_summary", {}),
            "penalty_simulation": result.get("penalty_simulation", {}),
            "adendum_reconciliation": result.get("adendum_reconciliation", {}),
            "contextual_extraction": result.get("contextual_extraction", {}),
            "ai_governance_metadata": ai_governance,
            "has_source_text": bool(request.all_document_text),
            "integrations": {"langflow": integration.get("status", "not_requested")},
        })
        return result


class PortfolioController:
    def __init__(self, portfolio: PortfolioService):
        self.portfolio = portfolio

    def overview(self) -> dict[str, Any]:
        return self.portfolio.overview()

    def list_audits(self, query: str = "", risk: str = "ALL") -> dict[str, Any]:
        return {"audits": self.portfolio.list_audits(query, risk)}
