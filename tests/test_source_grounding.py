from pathlib import Path
import pytest
from starlette.testclient import TestClient

from bidsentry.asgi import create_asgi_app
from bidsentry.config import Settings
from bidsentry.types.schemas import ValidationError
from bidsentry.generators.sanggahan_builder import _eligible, build_sanggahan_markdown


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    web_dir = workspace / "web"
    web_dir.mkdir()
    (web_dir / "app.js").write_text("console.log('test');", encoding="utf-8")
    (workspace / "index.html").write_text("<html><body>Test</body></html>", encoding="utf-8")
    env_file = workspace / ".env"
    env_file.write_text("# test env\n", encoding="utf-8")
    settings = Settings(
        workspace_root=workspace,
        static_root=web_dir,
        audit_log_path=workspace / "audit_log.jsonl",
        host="127.0.0.1",
        port=8000,
        max_request_bytes=1024 * 1024,
        langflow_url="http://localhost:7860",
        langflow_flow_id="",
        langflow_api_key="",
        langflow_enabled=False,
        langflow_timeout_seconds=5.0,
        gemini_api_key="",
        gemini_model="gemini-3.8-flash",
        llm_provider="",
        llm_api_key="",
        llm_model_name="",
        watsonx_project_id="",
        watsonx_url="https://us-south.ml.cloud.ibm.com",
        composio_api_key="",
        composio_base_url="https://backend.composio.dev/api/v3.1/tools/execute/{action}",
        composio_user_id="test",
        composio_timeout_seconds=5.0,
        bob_mcp_config_path=workspace / "mcp.json",
        access_token="",
        audit_retention_days=90,
    )
    return TestClient(create_asgi_app(settings), base_url="http://127.0.0.1:8000")


def test_quote_not_in_source_rejected_in_builder():
    source_text = "BAB III. SPESIFIKASI TEKNIS: Server harus memiliki 64 core CPU dan 256GB RAM."
    
    # Finding with fabricated quote that is NOT in source text
    fake_findings = [
        {
            "id": "SPEC-LOCKIN-PROC",
            "category": "Spesifikasi",
            "clause": "Penguncian Merek Server",
            "requirement_evidence": "Server wajib merek Dell PowerEdge R750 tanpa opsi merek lain",  # NOT in source!
            "status": "GAP",
        }
    ]
    
    eligible = _eligible(fake_findings, source_text)
    # The fake quote must be rejected and excluded from eligible
    assert len(eligible) == 0, "Kutipan yang tidak ada di sumber asli harus ditolak oleh _eligible"

    # Verbatim quote that IS in source text
    real_findings = [
        {
            "id": "SPEC-LOCKIN-PROC",
            "category": "Spesifikasi",
            "clause": "Ketentuan CPU",
            "requirement_evidence": "Server harus memiliki 64 core CPU",  # Exact substring!
            "status": "GAP",
        }
    ]
    eligible_real = _eligible(real_findings, source_text)
    assert len(eligible_real) == 1, "Kutipan exact substring dari sumber asli harus diterima"
    assert eligible_real[0]["verbatim_quote"] == "Server harus memiliki 64 core CPU"


def test_api_sanggahan_rejects_unverified_quote(client: TestClient):
    source_text = "BAB I. KETENTUAN UMUM: Pengadaan barang komputer kantor tahun 2026."
    payload = {
        "tender_id": "TND-TEST-001",
        "package_name": "Paket Komputer",
        "company_name": "PT Uji Coba",
        "notice_number": "NOT-001",
        "pokja_name": "Pokja Pengadaan",
        "source_text": source_text,
        "findings": [
            {
                "id": "SPEC-LOCKIN-PROC",
                "category": "Spesifikasi",
                "clause": "Penguncian Merek Khusus",
                "requirement_evidence": "Kutipan ini fiktif dan sama sekali tidak ada di dokumen sumber",
                "status": "GAP",
            }
        ],
        "format": "docx",
    }
    
    response = client.post("/api/v1/audit/sanggahan-doc", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "ditolak" in data["error"]["message"].lower() or "tidak ditemukan" in data["error"]["message"].lower()


def test_api_sanggahan_rejects_missing_source_text(client: TestClient):
    payload = {
        "tender_id": "TND-TEST-002",
        "package_name": "Paket Server",
        "company_name": "PT Uji Coba",
        "notice_number": "NOT-002",
        "pokja_name": "Pokja Pengadaan",
        "source_text": "",  # Empty source text
        "findings": [],
        "format": "docx",
    }
    
    response = client.post("/api/v1/audit/sanggahan-doc", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "tidak tersedia" in data["error"]["message"].lower() or "source_text" in str(data)
