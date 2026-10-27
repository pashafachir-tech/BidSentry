from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from bidsentry.api.routes import ApiRouter
from bidsentry.app import create_application
from bidsentry.config import Settings


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        base = Settings.from_environment()
        self._orig_composio_key = os.environ.get("COMPOSIO_API_KEY")
        if "COMPOSIO_API_KEY" in os.environ:
            del os.environ["COMPOSIO_API_KEY"]
        self.settings = replace(
            base,
            audit_log_path=Path(self.temp_dir.name) / "audit.jsonl",
            langflow_enabled=False,
            langflow_flow_id="",
            composio_api_key="",
        )
        self.app = create_application(self.settings)
        self.router = ApiRouter(self.app)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        if self._orig_composio_key is not None:
            os.environ["COMPOSIO_API_KEY"] = self._orig_composio_key
        elif "COMPOSIO_API_KEY" in os.environ:
            del os.environ["COMPOSIO_API_KEY"]

    def test_health_reports_local_fallback_without_optional_services(self) -> None:
        response = self.router.dispatch("GET", "/api/health")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["data"]["status"], "ok")
        self.assertFalse(response.body["data"]["integrations"]["langflow"]["configured"])
        self.assertFalse(response.body["data"]["integrations"]["ibm_bob"]["verified_end_to_end"])

    def test_integration_connection_check_is_read_only_when_services_are_unconfigured(self) -> None:
        response = self.router.dispatch("GET", "/api/settings/integrations/test")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["data"]["langflow"]["status"], "not_configured")
        self.assertEqual(response.body["data"]["composio"]["status"], "not_configured")

    def test_audit_requires_at_least_one_document(self) -> None:
        response = self.router.dispatch("POST", "/api/audit", payload={"package_name": "Empty"})
        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("request_id", response.body["meta"])

    def test_audit_returns_local_result_and_logs_no_document_text(self) -> None:
        secret_phrase = "Rencana pengadaan internal rahasia 2026; persyaratan KBLI 1234567890123456"
        response = self.router.dispatch("POST", "/api/audit", payload={
            "package_name": "Paket uji",
            "dok_pemilihan": secret_phrase,
            "pustaka": "Tidak ada dokumen perusahaan yang disertakan.",
        })
        self.assertEqual(response.status, 200)
        data = response.body["data"]
        self.assertEqual(data["risk_score"], 0)
        self.assertEqual(data["risk_level"], "LOW")
        self.assertEqual(data["verdict"], "GO")
        self.assertEqual(data["risk"]["method"], "deterministic evidence checks")
        self.assertEqual(data["findings"], [])
        self.assertIn("bukan pernyataan", data["executive_summary"]["qualification"])
        log_text = self.settings.audit_log_path.read_text(encoding="utf-8")
        self.assertNotIn("Rencana pengadaan internal rahasia", log_text)
        self.assertNotIn("1234567890123456", log_text)

    def test_empty_search_and_risk_filter_returns_no_mock_register(self) -> None:
        response = self.router.dispatch("GET", "/api/audits", "risk=HIGH")
        self.assertEqual(response.status, 200)
        rows = response.body["data"]["audits"]
        self.assertEqual(rows, [])

    def test_overview_contains_only_locally_saved_audits(self) -> None:
        response = self.router.dispatch("GET", "/api/overview")
        overview = response.body["data"]
        self.assertEqual(overview["total_audits"], 0)
        self.assertEqual(overview["audits"], [])
        self.assertEqual(overview["dataset_label"], "Audit lokal tersimpan")

    def test_dispatch_without_connector_returns_unavailable_without_fabricating_actions(self) -> None:
        response = self.router.dispatch("POST", "/api/dispatch", payload={
            "nama_paket": "Paket uji",
            "verdict": "REVIEW",
            "catatan": "Isi dokumen rahasia yang tidak boleh dicatat",
        })
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["data"]["status"], "unavailable")
        self.assertEqual(response.body["data"]["actions"], {})
        self.assertIn("tidak ada tindakan", response.body["data"]["message"])
        log_text = self.settings.audit_log_path.read_text(encoding="utf-8")
        self.assertIn("workspace.dispatch", log_text)
        self.assertNotIn("Isi dokumen rahasia", log_text)

    def test_unknown_route_and_wrong_method_are_consistent(self) -> None:
        missing = self.router.dispatch("GET", "/api/missing")
        wrong_method = self.router.dispatch("DELETE", "/api/audit")
        self.assertEqual(missing.status, 404)
        self.assertEqual(missing.body["error"]["code"], "NOT_FOUND")
        self.assertEqual(wrong_method.status, 405)
        self.assertEqual(wrong_method.body["error"]["code"], "METHOD_NOT_ALLOWED")


if __name__ == "__main__":
    unittest.main()
