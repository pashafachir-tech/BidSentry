"""Explicit API router with a single versioned response envelope.

Role separation (Pokja vs Vendor) is enforced here, on the server: the caller's
role comes from the signed session cookie resolved by the ASGI layer.

    Pokja  : Berita Acara (BAHE) draft, clarification letter to bidders
    Vendor : objection (sanggahan) draft
    Both   : create/read their own audits, proof log, BoQ and review workbooks
"""

from __future__ import annotations

import base64
import logging
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs

from pydantic import ValidationError as PydanticValidationError

from bidsentry import __version__
from bidsentry.app import Application
from bidsentry.core.auth import AuthError, Role, require_role
from bidsentry.generators._document_support import DocumentGenerationError, normalize_finding
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
from bidsentry.generators.sanggahan_builder import (
    _eligible,
    build_sanggahan_docx,
    build_sanggahan_html,
    build_sanggahan_markdown,
    build_sanggahan_pdf,
)
from bidsentry.schemas.audit_contracts import ClarificationDocumentRequest, MinutesEvaluationDocumentRequest
from bidsentry.schemas.comprehensive import ComprehensiveAuditRequest
from bidsentry.services import risk_engine
from bidsentry.services.comprehensive_audit_service import ComprehensiveAuditInputError
from bidsentry.types.responses import failure, success
from bidsentry.types.schemas import ValidationError

LOGGER = logging.getLogger("bidsentry.api")

MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "markdown": "text/markdown; charset=utf-8",
    "html": "text/html; charset=utf-8",
}
KNOWN_ROUTES = {
    "/api/health", "/api/integrations", "/api/settings/integrations", "/api/settings/integrations/test", "/api/overview",
    "/api/audits", "/api/export/workbook", "/api/export/boq", "/api/audit", "/api/v1/audit/evaluate", "/api/v1/audit/sanggahan-doc",
    "/api/v1/audit/comprehensive", "/api/v1/audit/clarification-doc", "/api/v1/audit/minutes-eval-doc", "/api/review-feedback",
    "/api/documents/extract", "/api/dispatch", "/api/risk/decision-table",
}


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any]
    headers: dict[str, str] | None = None


def _pydantic_details(exc: PydanticValidationError) -> list[dict[str, str]]:
    return [
        {"field": ".".join(str(part) for part in error.get("loc", ())), "issue": str(error.get("type", "invalid_value")), "message": str(error.get("msg", "Invalid value."))}
        for error in exc.errors(include_url=False)
    ]


def _encode(content: str | bytes, filename: str, output_format: str) -> dict[str, Any]:
    binary = content.encode("utf-8") if isinstance(content, str) else content
    return {"filename": filename, "content_type": MIME_TYPES[output_format], "content_base64": base64.b64encode(binary).decode("ascii"), "draft_only": True}


class ApiRouter:
    def __init__(self, app: Application):
        self.app = app

    def dispatch(self, method: str, path: str, raw_query: str = "", payload: Any = None, role: str | None = None) -> ApiResponse:
        request_id = str(uuid.uuid4())
        query = parse_qs(raw_query, keep_blank_values=True)
        try:
            data = self._route(method, path, query, payload, role)
            if isinstance(data, ApiResponse):
                return data
            return ApiResponse(200, success(data, request_id))
        except AuthError as exc:
            return ApiResponse(exc.status, failure(exc.code, exc.message, request_id))
        except ValidationError as exc:
            return ApiResponse(400, failure("VALIDATION_ERROR", exc.message, request_id, exc.details))
        except DocumentGenerationError as exc:
            return ApiResponse(503, failure("FEATURE_UNAVAILABLE", str(exc), request_id))
        except Exception:
            LOGGER.exception("Request %s failed on %s %s", request_id, method, path)
            return ApiResponse(500, failure("INTERNAL_ERROR", "The request could not be completed.", request_id))

    # ------------------------------------------------------------------ routes
    def _route(self, method: str, path: str, query: dict[str, list[str]], payload: Any, role: str | None) -> Any:
        if method == "GET" and path == "/api/health":
            return {"status": "ok", "version": __version__, "engine": "local-rules", "integrations": self._integrations()}
        if method == "GET" and path == "/api/integrations":
            return self._integrations()
        if method == "GET" and path == "/api/risk/decision-table":
            return {"method": "decision-table-v2", "rules": risk_engine.decision_table()}
        if method == "GET" and path == "/api/settings/integrations":
            return self.app.settings_service.public_settings(self.app.settings, self.app.settings_service.env_path.is_file())
        if method == "GET" and path == "/api/settings/integrations/test":
            from bidsentry.services.composio_dispatcher import test_composio_connection
            return {
                "watsonx": self.app.watsonx.test_connection(),
                "langflow": self.app.langflow.test_connection(),
                "composio": test_composio_connection(self.app.settings),
            }
        if method == "PUT" and path == "/api/settings/integrations":
            self.app.apply_settings(self.app.settings_service.save(payload))
            return self.app.settings_service.public_settings(self.app.settings, self.app.settings_service.env_path.is_file())
        if method == "GET" and path == "/api/overview":
            return self.app.portfolio.overview(role=role)
        if method == "GET" and path == "/api/audits":
            return self.app.portfolio.list_audits(self._one(query, "q"), self._one(query, "risk", "ALL"), role=role)
        if method == "GET" and path.startswith("/api/audits/") and path.endswith("/proof"):
            audit = self._load_audit(path.removeprefix("/api/audits/").removesuffix("/proof").strip("/"), role)
            return {
                "audit_id": audit.get("audit_id"),
                "steps": audit.get("proof_log", []),
                "summary": audit.get("proof_summary", {}),
                "risk": audit.get("risk", {}),
                "decision_table": risk_engine.decision_table(),
                "ai_governance": audit.get("ai_governance_metadata", {}),
                "documents": audit.get("documents", []),
            }
        if method == "GET" and (path == "/api/audit" or (path.startswith("/api/audits/") and len(path) > len("/api/audits/"))):
            audit_id = path.removeprefix("/api/audits/").strip() if path.startswith("/api/audits/") else self._one(query, "audit_id")
            return self._load_audit(audit_id, role)
        if method == "DELETE" and (path == "/api/audits" or path.startswith("/api/audits/")):
            audit_id = path.removeprefix("/api/audits/").strip() if path.startswith("/api/audits/") else (self._one(query, "audit_id") or (payload.get("audit_id") if isinstance(payload, dict) else None))
            if not audit_id:
                raise ValidationError("Audit ID wajib diisi.", [{"field": "audit_id", "issue": "required"}])
            self._load_audit(audit_id, role)
            if not self.app.audit_log.delete_audit(audit_id):
                raise ValidationError("Pemeriksaan tidak ditemukan atau sudah dihapus.", [{"field": "audit_id", "issue": "not_found"}])
            return {"audit_id": audit_id, "deleted": True}
        if method == "POST" and path == "/api/export/workbook":
            return self.app.workbook_export.create(payload)
        if method == "POST" and path == "/api/export/boq":
            current = require_role(role, Role.POKJA, Role.VENDOR)
            audit_id = payload.get("audit_id") if isinstance(payload, dict) else None
            audit = self._load_audit(str(audit_id or ""), current.value)
            source_text = self.app.audit_log.get_source_text(str(audit_id)) or ""
            return self.app.boq_export.create(audit, source_text, role=current.value)
        if method == "POST" and path in {"/api/audit", "/api/v1/audit/evaluate"}:
            return self.app.audit.create(payload, role=role)
        if method == "POST" and path == "/api/v1/audit/comprehensive":
            if not isinstance(payload, dict):
                raise ValidationError("Request audit komprehensif tidak valid.", [{"field": "$", "issue": "expected_object"}])
            try:
                request = ComprehensiveAuditRequest.model_validate(payload)
            except PydanticValidationError as exc:
                raise ValidationError("Request audit komprehensif tidak memenuhi skema.", _pydantic_details(exc)) from exc
            try:
                return self.app.comprehensive_audit.audit(request)
            except ComprehensiveAuditInputError as exc:
                raise ValidationError(str(exc), [{"field": "pdf_base64", "issue": "invalid_value"}]) from exc
        if method == "POST" and path == "/api/v1/audit/clarification-doc":
            require_role(role, Role.POKJA)
            return self._generate_clarification(payload, role)
        if method == "POST" and path == "/api/v1/audit/minutes-eval-doc":
            require_role(role, Role.POKJA)
            return self._generate_minutes(payload, role)
        if method == "POST" and path == "/api/v1/audit/sanggahan-doc":
            require_role(role, Role.VENDOR)
            return self._generate_sanggahan_document(payload, role)
        if method == "GET" and path == "/api/review-feedback":
            return self._feedback_with_assessment(self._one(query, "audit_id"))
        if method == "POST" and path == "/api/review-feedback":
            return self._record_feedback(payload)
        if method == "POST" and path == "/api/documents/extract":
            if not isinstance(payload, dict):
                raise ValidationError("Request unggah tidak valid.", [{"field": "$", "issue": "expected_object"}])
            return self.app.documents.extract(payload.get("filename", ""), payload.get("content", b""))
        if method == "POST" and path == "/api/dispatch":
            return self.app.dispatch.create(payload, require_external_consent=self.app.settings.composio_configured)
        request_id = str(uuid.uuid4())
        if path in KNOWN_ROUTES:
            return ApiResponse(405, failure("METHOD_NOT_ALLOWED", "HTTP method is not supported for this route.", request_id))
        return ApiResponse(404, failure("NOT_FOUND", "API route was not found.", request_id))

    # ----------------------------------------------------------------- helpers
    def _load_audit(self, audit_id: str, role: str | None) -> dict[str, Any]:
        if not audit_id:
            raise ValidationError("Audit ID wajib diisi.", [{"field": "audit_id", "issue": "required"}])
        audit = self.app.audit_log.get_audit(audit_id)
        if not audit:
            audit = next((row for row in self.app.portfolio.list_audits()["audits"] if row.get("audit_id") == audit_id), None)
        owner = (audit or {}).get("owner_role")
        if not audit or (role and owner and owner != role):
            # A Vendor must not be able to read a Pokja audit and vice versa.
            raise ValidationError("Pemeriksaan tidak ditemukan.", [{"field": "audit_id", "issue": "not_found"}])
        return audit

    def _reviewer_outcomes(self, audit_id: str) -> dict[str, str]:
        snapshot = self.app.audit_log.feedback_snapshot(audit_id)
        return {finding_id: value.get("outcome") for finding_id, value in (snapshot.get("outcomes") or {}).items()}

    def _with_outcomes(self, findings: list[dict[str, Any]], audit_id: str) -> list[dict[str, Any]]:
        outcomes = self._reviewer_outcomes(audit_id) if audit_id else {}
        return [{**item, "reviewer_outcome": outcomes.get(str(item.get("id")))} if outcomes.get(str(item.get("id"))) else item for item in findings]

    def _feedback_with_assessment(self, audit_id: str) -> dict[str, Any]:
        snapshot = self.app.audit_log.feedback_snapshot(audit_id)
        if audit_id:
            audit = self.app.audit_log.get_audit(audit_id)
            if audit and isinstance(audit.get("findings"), list):
                excluded = [finding_id for finding_id, value in (snapshot.get("outcomes") or {}).items() if value.get("outcome") == "NOT_SUPPORTED"]
                recognized = 0 if audit.get("verdict") == "TIDAK ADA SYARAT TERBACA" else max(1, len(audit["findings"]))
                snapshot["reviewed_assessment"] = risk_engine.assess(audit["findings"], requirements_recognized=recognized, excluded_finding_ids=excluded).model_dump(mode="json")
        return snapshot

    def _record_feedback(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request umpan balik tidak valid.", [{"field": "$", "issue": "expected_object"}])
        audit_id, finding_id, outcome = payload.get("audit_id"), payload.get("finding_id"), payload.get("outcome")
        if not isinstance(audit_id, str) or not audit_id.strip() or len(audit_id) > 80:
            raise ValidationError("Audit ID tidak valid.", [{"field": "audit_id", "issue": "invalid_value"}])
        if not isinstance(finding_id, str) or not finding_id.strip() or len(finding_id) > 80:
            raise ValidationError("Finding ID tidak valid.", [{"field": "finding_id", "issue": "invalid_value"}])
        if not isinstance(outcome, str) or outcome not in {"SUPPORTED", "NEEDS_MORE_INFO", "NOT_SUPPORTED"}:
            raise ValidationError("Pilih salah satu hasil review yang tersedia.", [{"field": "outcome", "issue": "invalid_value"}])
        if not self.app.audit_log.finding_exists(audit_id.strip(), finding_id.strip()):
            raise ValidationError("Temuan tidak cocok dengan audit lokal yang tercatat.", [{"field": "finding_id", "issue": "unknown_finding"}])
        self.app.audit_log.append({"event_type": "finding.reviewed", "audit_id": audit_id.strip(), "finding_id": finding_id.strip(), "outcome": outcome})
        return self._feedback_with_assessment(audit_id.strip())

    def _log_document(self, audit_id: str, kind: str, document: dict[str, Any], role: str | None, findings_included: int) -> None:
        if not audit_id:
            return
        import hashlib
        digest = hashlib.sha256(base64.b64decode(document["content_base64"])).hexdigest()
        document["sha256"] = digest
        self.app.audit_log.append({
            "event_type": "document.generated", "audit_id": audit_id, "document_kind": kind, "filename": document["filename"],
            "sha256": digest, "role": role, "findings_included": findings_included,
        })

    def _generate_minutes(self, payload: Any, role: str | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request dokumen tidak valid.", [{"field": "$", "issue": "expected_object"}])
        audit_id = str(payload.get("audit_id") or "").strip()
        audit = self._load_audit(audit_id, role) if audit_id else {}
        body = {key: value for key, value in payload.items() if key not in {"audit_id"}}
        body.setdefault("tender_id", audit.get("tender_id") or audit.get("package_name") or "TENDER")
        body.setdefault("vendor_name", audit.get("company_name") or "Peserta")
        if not body.get("findings") and audit:
            body["findings"] = self._with_outcomes(audit.get("findings", []), audit_id)
        try:
            model = MinutesEvaluationDocumentRequest.model_validate(body)
        except PydanticValidationError as exc:
            raise ValidationError("Request dokumen tidak memenuhi skema.", _pydantic_details(exc)) from exc
        builders = {"pdf": build_minutes_pdf, "docx": build_minutes_docx, "markdown": build_minutes_markdown, "html": build_minutes_html}
        meta = {"package_name": audit.get("package_name"), "pokja_name": audit.get("pokja_name"), "audit_id": audit_id or None}
        content = builders[model.format](model.tender_id, model.vendor_name, model.findings, model.legal_mappings, risk=audit.get("risk"), meta=meta)
        document = _encode(content, "berita-acara-hasil-evaluasi-draft." + model.format, model.format)
        self._log_document(audit_id, "berita_acara", document, role, len(model.findings))
        return document

    def _generate_clarification(self, payload: Any, role: str | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request dokumen tidak valid.", [{"field": "$", "issue": "expected_object"}])
        audit_id = str(payload.get("audit_id") or "").strip()
        audit = self._load_audit(audit_id, role) if audit_id else {}
        findings = payload.get("anomalies", payload.get("findings"))
        if not findings and audit:
            findings = [item for item in audit.get("findings", []) if item.get("status") in {"GAP", "REVIEW", "EXPIRING"}]
        anomalies = []
        for item in findings or []:
            if isinstance(item, dict) and "anomaly_type" not in item and ("clause" in item or "requirement_evidence" in item):
                row = normalize_finding(item)
                item = {"anomaly_type": f"{row['code']} — {row['title']}", "source_quote": row["quote"], "page_ref": row["locator"], "description": row["note"]}
            anomalies.append(item)
        try:
            model = ClarificationDocumentRequest.model_validate({
                "tender_id": payload.get("tender_id") or audit.get("tender_id") or audit.get("package_name") or "TENDER",
                "vendor_name": payload.get("vendor_name") or audit.get("company_name") or "Peserta",
                "format": payload.get("format", "docx"),
                "anomalies": anomalies,
            })
        except PydanticValidationError as exc:
            raise ValidationError("Request dokumen tidak memenuhi skema.", _pydantic_details(exc)) from exc
        builders = {"pdf": build_clarification_pdf, "docx": build_clarification_docx, "markdown": build_clarification_markdown, "html": build_clarification_html}
        document = _encode(builders[model.format](model.tender_id, model.vendor_name, model.anomalies), "surat-permintaan-klarifikasi." + model.format, model.format)
        self._log_document(audit_id, "klarifikasi", document, role, len(model.anomalies))
        return document

    def _generate_sanggahan_document(self, payload: Any, role: str | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError("Request sanggahan harus berupa objek.", [{"field": "$", "issue": "expected_object"}])
        allowed = {"tender_id", "package_name", "company_name", "notice_number", "pokja_name", "source_text", "audit_id", "findings", "legal_citations", "format"}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValidationError("Kolom sanggahan tidak dikenal.", [{"field": key, "issue": "unknown_field"} for key in unknown])
        audit_id = str(payload.get("audit_id", "")).strip()
        audit = self._load_audit(audit_id, role) if audit_id and self.app.audit_log.get_audit(audit_id) else {}
        source_text = payload.get("source_text", "")
        if (not source_text or not str(source_text).strip()) and audit_id:
            source_text = self.app.audit_log.get_source_text(audit_id) or ""
        if not isinstance(source_text, str) or not source_text.strip() or len(source_text) > 5_000_000:
            raise ValidationError(
                "Teks sumber asli tidak tersedia untuk audit ini. Draf sanggahan memerlukan teks sumber asli untuk verifikasi kutipan.",
                [{"field": "source_text", "issue": "source_text_unavailable"}],
            )
        findings = payload.get("findings")
        if not findings and audit:
            findings = audit.get("findings", [])
        findings = findings or []
        if not isinstance(findings, list) or len(findings) > 1000 or any(not isinstance(item, dict) for item in findings):
            raise ValidationError("Daftar temuan tidak valid.", [{"field": "findings", "issue": "invalid_value"}])
        findings = self._with_outcomes(findings, audit_id)
        eligible = _eligible(findings, source_text)
        if findings and not eligible:
            raise ValidationError(
                "Tidak ada temuan yang dapat disanggah: hanya kesenjangan terkonfirmasi pada dokumen tender dengan kutipan persis di teks sumber yang dimasukkan (kutipan lain ditolak).",
                [{"field": "findings", "issue": "no_grounded_findings"}],
            )
        output_format = payload.get("format", "docx")
        if output_format not in MIME_TYPES:
            raise ValidationError("Format harus docx, pdf, markdown, atau html.", [{"field": "format", "issue": "invalid_value"}])
        kwargs: dict[str, Any] = {}
        for key in ("tender_id", "package_name", "company_name", "notice_number", "pokja_name"):
            value = payload.get(key) or audit.get(key) or ""
            if not isinstance(value, str) or len(value) > 500:
                raise ValidationError("Metadata sanggahan tidak valid.", [{"field": key, "issue": "invalid_value"}])
            kwargs[key] = value
        citations = payload.get("legal_citations", [])
        if not isinstance(citations, list) or any(not isinstance(item, dict) for item in citations):
            raise ValidationError("legal_citations harus berupa daftar objek.", [{"field": "legal_citations", "issue": "invalid_value"}])
        kwargs.update(source_text=source_text, findings=eligible, legal_citations=citations)
        builders = {"docx": build_sanggahan_docx, "pdf": build_sanggahan_pdf, "markdown": build_sanggahan_markdown, "html": build_sanggahan_html}
        document = _encode(builders[output_format](**kwargs), f"draf-sanggahan.{output_format}", output_format)
        document["findings_included"] = [item.get("id") for item in eligible]
        self._log_document(audit_id, "sanggahan", document, role, len(eligible))
        return document

    def _integrations(self) -> dict[str, Any]:
        settings = self.app.settings
        return {
            "audit_engine": {"status": "ready", "mode": "local rules"},
            "langflow": self.app.langflow.status(),
            "watsonx": self.app.watsonx.status(),
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
