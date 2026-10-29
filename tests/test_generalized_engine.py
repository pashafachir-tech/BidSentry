"""Tests for generalized detection rules, PII scrubbing, audit log hash chaining, and watsonx preflight guardrails."""

import json
import tempfile
from pathlib import Path
import pytest

from bidsentry.config import Settings
from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest
from bidsentry.lib.audit_log import AuditLog
from bidsentry.lib.pii import contains_unmasked_pii, mask_text
from bidsentry.services.watsonx_service import WatsonxService


@pytest.fixture
def engine():
    return EvaluationEngine()


class TestBrandLockinGeneralization:
    def test_brand_lockin_lenovo(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Teknis:\n1. Spesifikasi laptop wajib merek Lenovo ThinkPad X1 untuk seluruh staf operasional."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-BRAND-LOCKIN" in finding_ids

    def test_brand_lockin_toyota(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Kendaraan:\n1. Wajib Toyota Innova Zenix untuk armada dinas lapangan."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-BRAND-LOCKIN" in finding_ids

    def test_brand_lockin_cisco(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Jaringan:\n1. Switch core wajib Cisco Catalyst 9300 48-port PoE."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-LOCKIN-NETWORKING" in finding_ids

    def test_brand_lockin_oracle(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Database:\n1. Server basis data wajib Oracle Database 19c Enterprise Edition."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-LOCKIN-SOFTWARE" in finding_ids

    def test_brand_lockin_intel_xeon_gold(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Server:\n1. Menggunakan prosesor wajib Intel Xeon Gold 6430 dual socket."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-LOCKIN-CPU" in finding_ids

    def test_brand_lockin_nvidia_a100(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Server AI:\n1. Wajib NVIDIA A100 80GB SXM4 4 unit."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-LOCKIN-GPU" in finding_ids

    def test_anti_equivalency_negation_detected(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan GPU:\n1. Server komputasi NVIDIA H100 SXM5 tidak menerima produk setara."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-LOCKIN-GPU" in finding_ids

    def test_valid_equivalency_safe_harbor(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Kendaraan:\n1. Kebutuhan kendaraan berupa sekelas Toyota Innova Zenix atau kendaraan sejenis yang setara.",
            pustaka="Kendaraan MPV 2000cc sekelas setara siap disediakan."
        )
        res = engine.evaluate(req)
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-BRAND-LOCKIN" not in finding_ids


class TestRegionalLockinAndConflictOfInterest:
    def test_regional_domicile_lockin(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Kualifikasi:\n1. Keanggotaan asosiasi/domisili Kalsel saja yang diperkenankan mendaftar tender ini."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-REGIONAL-LOCKIN" in finding_ids

    def test_conflict_of_interest_familial(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Persyaratan Khusus:\n1. Penyedia wajib bermitra dengan vendor lokal milik keponakan Kepala Dinas untuk subkontrak."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "GOV-CONFLICT-INTEREST" in finding_ids


class TestTimelineAndNarrativeBudget:
    def test_timeline_word_numbers(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Jadwal Pengadaan:\n1. Pemasukan penawaran tiga hari kerja sejak pengumuman lelang."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "PROC-TIMELINE-COMPRESSED" in finding_ids

    def test_narrative_budget_words(self, engine):
        req = EvaluationRequest(
            dok_pemilihan="Anggaran Pengadaan:\nPagu Anggaran Rp 1,2 miliar.\nTotal BoQ Rp 1,5 miliar."
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        finding_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "FIN-OVER-BUDGET" in finding_ids


class TestPiiScrubbingAndHashChain:
    def test_standalone_nik_and_bank_account_masking(self):
        sample = "Pemenang NIK 6371012345678901 atas nama Budi Santoso, Rek. BCA 1234567890, nilai Rp 10.000.000.000."
        masked = mask_text(sample)
        assert "6371012345678901" not in masked
        assert "[NIK-REDACTED]" in masked
        assert "1234567890" not in masked
        assert "[ACCOUNT-REDACTED]" in masked
        assert "Rp 10.000.000.000" in masked

    def test_audit_log_hash_chain_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit_chain.jsonl"
            audit = AuditLog(log_file)
            audit.append({"action": "INIT", "detail": "Audit engine started"})
            audit.append({"action": "SCAN", "detail": "Doc evaluated", "verdict": "NO-GO"})

            # Verify legitimate chain
            is_valid, count, msg = audit.verify_chain()
            assert is_valid is True
            assert count == 2
            assert "verified successfully" in msg

            # Tamper record
            lines = log_file.read_text(encoding="utf-8").splitlines()
            tampered_record = json.loads(lines[0])
            tampered_record["detail"] = "TAMPERED DETAIL"
            lines[0] = json.dumps(tampered_record)
            log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # Verify tamper detection
            is_valid_tampered, count_tampered, msg_tampered = audit.verify_chain()
            assert is_valid_tampered is False
            assert "Tampered record on line 1" in msg_tampered


class TestWatsonxPreflightGuardrails:
    def test_preflight_grounding_and_pii_check(self):
        service = WatsonxService(Settings.from_environment())
        source = "Klausul 1: Jaminan penawaran 2% dari HPS. Klausul 2: SBU aktif."
        quotes = ["Jaminan penawaran 2% dari HPS", "Hallucinated quote not in text"]

        preflight = service.evaluate_preflight_guardrails(
            document_text=source,
            candidate_quotes=quotes,
        )
        assert preflight["local_guardrails_status"] == "ACTIVE_DETERMINISTIC"
        assert preflight["cloud_watsonx_governance_status"] == "ENTERPRISE_ROADMAP"
        assert preflight["grounding_check"]["quotes_evaluated"] == 2
        assert preflight["grounding_check"]["verbatim_grounded"] == 1
        assert preflight["grounding_check"]["unverified_or_rejected"] == 1
        assert preflight["pii_scrubbing"]["unmasked_pii_detected"] is False
