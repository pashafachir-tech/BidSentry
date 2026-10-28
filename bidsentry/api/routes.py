"""Small explicit API router with a single versioned response envelope."""

from __future__ import annotations

import json
import logging
import base64
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs

from bidsentry import __version__
from bidsentry.app import Application
from bidsentry.generators.clarification_doc import (
    build_clarification_docx,
    build_clarification_html,
    build_clarification_markdown,
    build_clarification_pdf,
)
from bidsentry.generators.minutes_eval_doc import (
    build_minutes_docx,
    build_minutes_html,
    build_minutes_markdown,
    build_minutes_pdf,
)
from bidsentry.generators.sanggahan_builder import build_sanggahan_docx, build_sanggahan_html, build_sanggahan_markdown, build_sanggahan_pdf
from bidsentry.generators._document_support import DocumentGenerationError
from bidsentry.schemas.comprehensive import ComprehensiveAuditRequest
from bidsentry.schemas.audit_contracts import ClarificationDocumentRequest, MinutesEvaluationDocumentRequest
from bidsentry.services.comprehensive_audit_service import ComprehensiveAuditInputError
from bidsentry.types.responses import failure, success
from bidsentry.types.schemas import ValidationError
from pydantic import ValidationError as PydanticValidationError


LOGGER = logging.getLogger("bidsentry.api")


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any]
    headers: dict[str, str] | None = None


class ApiRouter:
    def __init__(self, app: Application):
        self.app = app

    def dispatch(self, method: str, path: str, raw_query: str = "", payload: Any = None) -> ApiResponse:
        request_id = str(uuid.uuid4())
        query = parse_qs(raw_query, keep_blank_values=True)
        try:
            if method == "GET" and path == "/api/health":
                integrations = self._integrations()
                data = {"status": "ok", "version": __version__, "engine": "local-rules", "integrations": integrations}
            elif method == "GET" and path == "/api/integrations":
                data = self._integrations()
            elif method == "GET" and path == "/api/settings/integrations":
                data = self.app.settings_service.public_settings(self.app.settings, self.app.settings_service.env_path.is_file())
            elif method == "GET" and path == "/api/settings/integrations/test":
                from composio_dispatcher import test_composio_connection
                data = {
                    "langflow": self.app.langflow.test_connection(),
                    "composio": test_composio_connection(self.app.settings),
                }
            elif method == "PUT" and path == "/api/settings/integrations":
                self.app.settings = self.app.settings_service.save(payload)
                self.app.langflow.settings = self.app.settings
                data = self.app.settings_service.public_settings(self.app.settings, self.app.settings_service.env_path.is_file())
            elif method == "GET" and path == "/api/overview":
                data = self.app.portfolio.overview()
            elif method == "GET" and path == "/api/audits":
                data = self.app.portfolio.list_audits(self._one(query, "q"), self._one(query, "risk", "ALL"))
            elif method == "GET" and (path == "/api/audit" or (path.startswith("/api/audits/") and len(path) > len("/api/audits/"))):
                audit_id = path.removeprefix("/api/audits/").strip() if path.startswith("/api/audits/") else self._one(query, "audit_id")
                if not audit_id:
                    raise ValidationError("Audit ID wajib diisi.", [{"field": "audit_id", "issue": "required"}])
                audit_data = self.app.audit_log.get_audit(audit_id)
                if not audit_data:
                    row = next((r for r in self.app.portfolio.list_audits() if r.get("audit_id") == audit_id), None)
                    if row:
                        audit_data = row
                    else:
                        raise ValidationError("Pemeriksaan tidak ditemukan.", [{"field": "audit_id", "issue": "not_found"}])
                data = audit_data
            elif method == "DELETE" and (path == "/api/audits" or path.startswith("/api/audits/")):
                audit_id = path.removeprefix("/api/audits/").strip() if path.startswith("/api/audits/") else (self._one(query, "audit_id") or (payload.get("audit_id") if isinstance(payload, dict) else None))
                if not audit_id:
                    raise ValidationError("Audit ID wajib diisi.", [{"field": "audit_id", "issue": "required"}])
                deleted = self.app.audit_log.delete_audit(audit_id)
                if not deleted:
                    raise ValidationError("Pemeriksaan tidak ditemukan atau sudah dihapus.", [{"field": "audit_id", "issue": "not_found"}])
                data = {"audit_id": audit_id, "deleted": True}
            elif method == "POST" and path == "/api/export/workbook":
                data = self.app.workbook_export.create(payload)
            elif method == "POST" and path == "/api/audit":
                data = self.app.audit.create(payload)
            elif method == "POST" and path == "/api/v1/audit/evaluate":
                data = self.app.audit.create(payload)
            elif method == "POST" and path == "/api/v1/audit/comprehensive":
                if not isinstance(payload, dict):
                    raise ValidationError("Request audit komprehensif tidak valid.", [{"field": "$", "issue": "expected_object"}])
                try:
                    request = ComprehensiveAuditRequest.model_validate(payload)
                except PydanticValidationError as exc:
                    details = [
                        {"field": ".".join(str(part) for part in error.get("loc", ())), "issue": str(error.get("type", "invalid_value")), "message": str(error.get("msg", "Invalid value."))}
                        for error in exc.errors(include_url=False)
                    ]
                    raise ValidationError("Request audit komprehensif tidak memenuhi skema.", details) from exc
                try:
                    data = self.app.comprehensive_audit.audit(request)
                except ComprehensiveAuditInputError as exc:
                    raise ValidationError(str(exc), [{"field": "pdf_base64", "issue": "invalid_value"}]) from exc
            elif method == "POST" and path in {"/api/v1/audit/clarification-doc", "/api/v1/audit/minutes-eval-doc"}:
                data = self._generate_review_document(path, payload)
            elif method == "POST" and path == "/api/v1/audit/sanggahan-doc":
                data = self._generate_sanggahan_document(payload)
            elif method == "GET" and path == "/api/review-feedback":
                data = self.app.audit_log.feedback_snapshot(self._one(query, "audit_id"))
            elif method == "POST" and path == "/api/review-feedback":
                if not isinstance(payload, dict):
                    raise ValidationError("Request umpan balik tidak valid.", [{"field": "$", "issue": "expected_object"}])
                audit_id = payload.get("audit_id")
                finding_id = payload.get("finding_id")
                outcome = payload.get("outcome")
                if not isinstance(audit_id, str) or not audit_id.strip() or len(audit_id) > 80:
                    raise ValidationError("Audit ID tidak valid.", [{"field": "audit_id", "issue": "invalid_value"}])
                if not isinstance(finding_id, str) or not finding_id.strip() or len(finding_id) > 80:
                    raise ValidationError("Finding ID tidak valid.", [{"field": "finding_id", "issue": "invalid_value"}])
                if not isinstance(outcome, str) or outcome not in {"SUPPORTED", "NEEDS_MORE_INFO", "NOT_SUPPORTED"}:
                    raise ValidationError("Pilih salah satu hasil review yang tersedia.", [{"field": "outcome", "issue": "invalid_value"}])
                if not self.app.audit_log.finding_exists(audit_id.strip(), finding_id.strip()):
                    raise ValidationError("Temuan tidak cocok dengan audit lokal yang tercatat.", [{"field": "finding_id", "issue": "unknown_finding"}])
                self.app.audit_log.append({
                    "event_type": "finding.reviewed",
                    "audit_id": audit_id.strip(),
                    "finding_id": finding_id.strip(),
                    "outcome": outcome,
                })
                data = self.app.audit_log.feedback_snapshot(audit_id.strip())
            elif method == "POST" and path == "/api/documents/extract":
                if not isinstance(payload, dict):
                    raise ValidationError("Request unggah tidak valid.", [{"field": "$", "issue": "expected_object"}])
                data = self.app.documents.extract(payload.get("filename", ""), payload.get("content", b""))
            elif method == "POST" and path == "/api/dispatch":
                data = self.app.dispatch.create(payload, require_external_consent=self.app.settings.composio_configured)
            elif path in {"/api/health", "/api/integrations", "/api/settings/integrations", "/api/settings/integrations/test", "/api/overview", "/api/audits", "/api/export/workbook", "/api/audit", "/api/v1/audit/evaluate", "/api/v1/audit/sanggahan-doc", "/api/v1/audit/comprehensive", "/api/v1/audit/clarification-doc", "/api/v1/audit/minutes-eval-doc", "/api/review-feedback", "/api/documents/extract", "/api/dispatch"}:
                return ApiResponse(405, failure("METHOD_NOT_ALLOWED", "HTTP method is not supported for this route.", request_id))
            else:
                return ApiResponse(404, failure("NOT_FOUND", "API route was not found.", request_id))
            return ApiResponse(200, success(data, request_id))
        except ValidationError as exc:
            return ApiResponse(400, failure("VALIDATION_ERROR", exc.message, request_id, exc.details))
        except DocumentGenerationError as exc:
            return ApiResponse(503, failure("FEATURE_UNAVAILABLE", str(exc), request_id))
        except Exception:
            LOGGER.exception("Request %s failed on %s %s", request_id, method, path)
            return ApiResponse(500, failure("INTERNAL_ERROR", "The request could not be completed.", request_id))

    @staticmethod
    def _generate_review_document(path: str, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request dokumen tidak valid.", [{"field": "$", "issue": "expected_object"}])
        try:
            model = (
                ClarificationDocumentRequest.model_validate({"tender_id": payload.get("tender_id"), "vendor_name": payload.get("vendor_name"), "format": payload.get("format", "docx"), "anomalies": payload.get("anomalies", payload.get("findings", []))})
                if path.endswith("clarification-doc") else
                MinutesEvaluationDocumentRequest.model_validate(payload)
            )
        except PydanticValidationError as exc:
            details = [{"field": ".".join(str(part) for part in error.get("loc", ())), "issue": str(error.get("type", "invalid_value")), "message": str(error.get("msg", "Invalid value."))} for error in exc.errors(include_url=False)]
            raise ValidationError("Request dokumen tidak memenuhi skema.", details) from exc
        tender_id, vendor_name, output_format = model.tender_id, model.vendor_name, model.format
        if path.endswith("clarification-doc"):
            findings = model.anomalies
            builders = {
                "pdf": build_clarification_pdf,
                "docx": build_clarification_docx,
                "markdown": build_clarification_markdown,
                "html": build_clarification_html,
            }
            content = builders[output_format](tender_id, vendor_name, findings)
            filename = "surat-permintaan-klarifikasi." + output_format
        else:
            findings, legal = model.findings, model.legal_mappings
            builders = {
                "pdf": build_minutes_pdf,
                "docx": build_minutes_docx,
                "markdown": build_minutes_markdown,
                "html": build_minutes_html,
            }
            content = builders[output_format](tender_id, vendor_name, findings, legal)
            filename = "berita-acara-hasil-evaluasi-draft." + output_format
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "markdown": "text/markdown; charset=utf-8",
            "html": "text/html; charset=utf-8",
        }
        binary_content = content.encode("utf-8") if isinstance(content, str) else content
        return {"filename": filename, "content_type": mime_types[output_format], "content_base64": base64.b64encode(binary_content).decode("ascii"), "draft_only": True}

    def _generate_sanggahan_document(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request sanggahan harus berupa objek.", [{"field": "$", "issue": "expected_object"}])
        allowed = {"tender_id", "package_name", "company_name", "notice_number", "pokja_name", "source_text", "audit_id", "findings", "legal_citations", "format"}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValidationError("Kolom sanggahan tidak dikenal.", [{"field": key, "issue": "unknown_field"} for key in unknown])
        source_text = payload.get("source_text", "")
        audit_id = str(payload.get("audit_id", "")).strip()
        if (not source_text or not str(source_text).strip()) and audit_id:
            audit = self.app.audit_log.get_audit(audit_id)
            if audit and audit.get("source_text"):
                source_text = audit["source_text"]

        if not isinstance(source_text, str) or not source_text.strip() or len(source_text) > 5_000_000:
            raise ValidationError(
                "Teks sumber asli tidak tersedia untuk audit ini. Draf sanggahan memerlukan teks sumber asli untuk verifikasi kutipan.",
                [{"field": "source_text", "issue": "source_text_unavailable"}]
            )

        findings = payload.get("findings", [])
        output_format = payload.get("format", "docx")
        if not isinstance(findings, list) or len(findings) > 1000 or any(not isinstance(item, dict) for item in findings):
            raise ValidationError("Daftar temuan tidak valid.", [{"field": "findings", "issue": "invalid_value"}])

        from bidsentry.generators.sanggahan_builder import _eligible
        eligible = _eligible(findings, source_text)
        if findings and not eligible:
            raise ValidationError(
                "Semua kutipan temuan ditolak karena tidak ditemukan secara persis di teks sumber asli.",
                [{"field": "findings", "issue": "no_grounded_findings"}]
            )

        if output_format not in {"docx", "pdf", "markdown", "html"}:
            raise ValidationError("Format harus docx, pdf, markdown, atau html.", [{"field": "format", "issue": "invalid_value"}])
        for key in ("tender_id", "package_name", "company_name", "notice_number", "pokja_name"):
            if not isinstance(payload.get(key, ""), str) or len(payload.get(key, "")) > 500:
                raise ValidationError("Metadata sanggahan tidak valid.", [{"field": key, "issue": "invalid_value"}])
        citations = payload.get("legal_citations", [])
        if not isinstance(citations, list) or any(not isinstance(item, dict) for item in citations):
            raise ValidationError("legal_citations harus berupa daftar objek.", [{"field": "legal_citations", "issue": "invalid_value"}])
        kwargs = {key: payload.get(key, "") for key in ("tender_id", "package_name", "company_name", "notice_number", "pokja_name")}
        kwargs.update(source_text=source_text, findings=eligible, legal_citations=citations)
        builders = {"docx": build_sanggahan_docx, "pdf": build_sanggahan_pdf, "markdown": build_sanggahan_markdown, "html": build_sanggahan_html}
        content = builders[output_format](**kwargs)
        mime_types = {"docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "pdf": "application/pdf", "markdown": "text/markdown; charset=utf-8", "html": "text/html; charset=utf-8"}
        binary = content.encode("utf-8") if isinstance(content, str) else content
        return {"filename": f"draf-sanggahan.{output_format}", "content_type": mime_types[output_format], "content_base64": base64.b64encode(binary).decode("ascii"), "draft_only": True}

    def _integrations(self) -> dict[str, Any]:
        settings = self.app.settings
        return {
            "audit_engine": {"status": "ready", "mode": "local rules"},
            "langflow": self.app.langflow.status(),
            "composio": {
                "configured": settings.composio_configured,
                "mode": "configured_not_verified" if settings.composio_configured else "not_configured",
                "verified_end_to_end": False,
            },
            "ibm_bob": {
                "mcp_config_present": settings.bob_mcp_config_path.is_file(),
                "mode": "MCP client configuration",
                "verified_end_to_end": False,
            },
        }

    @staticmethod
    def _one(query: dict[str, list[str]], key: str, default: str = "") -> str:
        values = query.get(key, [])
        return values[0] if values else default
