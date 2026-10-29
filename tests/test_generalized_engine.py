"""Tests for generalized detection rules, PII scrubbing, audit log hash chaining, watsonx preflight guardrails,
and newly expanded regional discrimination and English clause suites.
"""

from __future__ import annotations

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


# ===========================================================================
# Expanded Generalized Rule Suites (Tugas 4.1 & 4.2)
# ===========================================================================

class TestExpandedRegionalDiscrimination:
    def test_regional_lockin_positive_domicile(self, engine: EvaluationEngine) -> None:
        """Positive: Mandating legal domicile in a specific province/region must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Pengadaan Jasa Konsultansi Perencanaan",
            tender_id="TND-REG-01",
            dok_pemilihan=(
                "Kualifikasi Penyedia:\n"
                "Penyedia wajib berdomisili di wilayah Jawa Barat dan melampirkan surat domisili resmi.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-REGIONAL-LOCKIN" in gap_ids

    def test_regional_lockin_positive_branch_and_kadin(self, engine: EvaluationEngine) -> None:
        """Positive: Requiring local branch office and local chamber membership must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Pekerjaan Pemeliharaan Gedung",
            tender_id="TND-REG-02",
            dok_pemilihan=(
                "Kualifikasi Peserta:\n"
                "Penyedia harus memiliki kantor cabang di Surabaya dan terdaftar sebagai anggota KADIN Kota Surabaya.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-REGIONAL-LOCKIN" in gap_ids

    def test_regional_lockin_trap_legitimate_workshop(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: Legitimate physical site requirement (workshop/bengkel) must PASS as GO."""
        req = EvaluationRequest(
            package_name="Pengadaan Sewa dan Pemeliharaan Alat Berat",
            tender_id="TND-REG-03",
            dok_pemilihan=(
                "Ketentuan Fasilitas:\n"
                "Lokasi pekerjaan di Kota Bandung. Penyedia harus memiliki workshop/bengkel kerja di lokasi pekerjaan untuk perawatan teknis berkala.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-REGIONAL-LOCKIN" not in gap_ids

    def test_regional_lockin_trap_project_execution_site(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: Mentioning geographic location of project site must PASS as GO."""
        req = EvaluationRequest(
            package_name="Pembangunan Dermaga Pelabuhan",
            tender_id="TND-REG-04",
            dok_pemilihan=(
                "Lingkup Pekerjaan:\n"
                "Pekerjaan dilaksanakan di area pelabuhan Tanjung Perak Surabaya. Tempat pelaksanaan pekerjaan di Jawa Timur.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-REGIONAL-LOCKIN" not in gap_ids


class TestExpandedEnglishTimeline:
    def test_english_timeline_positive_compressed_period(self, engine: EvaluationEngine) -> None:
        """Positive: Compressed bidding and objection periods in English must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Server Infrastructure Procurement",
            tender_id="TND-EN-TIME-01",
            dok_pemilihan=(
                "Procurement Schedule:\n"
                "Tender timeline: bidding period 3 working days, objection period 2 working days.\n"
                "All submissions must be uploaded via the electronic procurement system."
            ),
            contract_draft="Liquidated damages of 1/1000 per day capped at 5% of contract value.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "PROC-TIMELINE-COMPRESSED" in gap_ids

    def test_english_timeline_positive_submission_deadline(self, engine: EvaluationEngine) -> None:
        """Positive: Short submission deadline in English must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Data Center Network Upgrade",
            tender_id="TND-EN-TIME-02",
            dok_pemilihan=(
                "Instructions to Bidders:\n"
                "The submission deadline is only 4 days from announcement date.\n"
                "Objection period is 5 working days."
            ),
            contract_draft="Liquidated damages of 1/1000 per day capped at 5% of contract value.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "PROC-TIMELINE-COMPRESSED" in gap_ids

    def test_english_timeline_trap_adequate_working_days(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: Adequate bidding and objection periods in English must PASS as GO."""
        req = EvaluationRequest(
            package_name="Core Switch Modernization",
            tender_id="TND-EN-TIME-03",
            dok_pemilihan=(
                "Procurement Schedule:\n"
                "Tender timeline: bidding period 10 working days, objection period 7 working days.\n"
                "Electronic documents will be accepted until 17:00 WIB."
            ),
            contract_draft="Liquidated damages of 1/1000 per day capped at 5% of contract value.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "PROC-TIMELINE-COMPRESSED" not in gap_ids

    def test_english_timeline_trap_adequate_calendar_days(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: Adequate submission window (14 calendar days) must PASS as GO."""
        req = EvaluationRequest(
            package_name="Cloud Security Assessment",
            tender_id="TND-EN-TIME-04",
            dok_pemilihan=(
                "Tender Rules:\n"
                "The submission deadline is 14 calendar days from announcement. Objection period is 7 working days."
            ),
            contract_draft="Liquidated damages of 1/1000 per day capped at 5% of contract value.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "PROC-TIMELINE-COMPRESSED" not in gap_ids


class TestExpandedEnglishBrandLockin:
    def test_english_brand_lockin_positive_must_be(self, engine: EvaluationEngine) -> None:
        """Positive: 'must be [brand], only [brand] accepted' without equivalency must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Enterprise Server Expansion",
            tender_id="TND-EN-LOCK-01",
            dok_pemilihan=(
                "Hardware Specifications:\n"
                "The server must be Dell PowerEdge R760, and only Dell accepted without alternative.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert any(x in gap_ids for x in ("SPEC-BRAND-LOCKIN", "SPEC-LOCKIN-MGMT"))

    def test_english_brand_lockin_positive_exclusive_use(self, engine: EvaluationEngine) -> None:
        """Positive: 'exclusive use of Cisco switches' without substitution must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Campus Network Backbone",
            tender_id="TND-EN-LOCK-02",
            dok_pemilihan=(
                "Network Equipment Requirements:\n"
                "Exclusive use of Cisco switches without substitution is required.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert any(x in gap_ids for x in ("SPEC-LOCKIN-NETWORKING", "SPEC-BRAND-LOCKIN"))

    def test_english_brand_lockin_trap_equal_or_better(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: 'or equivalent with equal or better specifications' must PASS as GO."""
        req = EvaluationRequest(
            package_name="Compute Node Expansion",
            tender_id="TND-EN-LOCK-03",
            dok_pemilihan=(
                "Technical Requirements:\n"
                "The server must be Dell PowerEdge R760, or equivalent with equal or better specifications.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-BRAND-LOCKIN" not in gap_ids

    def test_english_brand_lockin_trap_acceptable_alternative(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: 'or acceptable alternative' compliant with IEEE standards must PASS as GO."""
        req = EvaluationRequest(
            package_name="Distribution Switch Upgrade",
            tender_id="TND-EN-LOCK-04",
            dok_pemilihan=(
                "Switching Specifications:\n"
                "Exclusive use of Cisco switches or acceptable alternative meeting open IEEE standards.\n"
                "Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja."
            ),
            contract_draft="Denda 1/1000 per hari dengan batas maksimal 5% dari nilai kontrak.",
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "SPEC-BRAND-LOCKIN" not in gap_ids
        assert "SPEC-LOCKIN-NETWORKING" not in gap_ids


class TestExpandedEnglishLiquidatedDamages:
    def test_english_penalty_positive_without_limit(self, engine: EvaluationEngine) -> None:
        """Positive: 'liquidated damages of 1% per day without limit' must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="Custom Software Development",
            tender_id="TND-EN-PEN-01",
            dok_pemilihan="Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja.",
            contract_draft=(
                "General Conditions of Contract:\n"
                "Liquidated damages of 1% per day without limit for any delay in project milestone."
            ),
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "CON-PENALTY" in gap_ids

    def test_english_penalty_positive_uncapped(self, engine: EvaluationEngine) -> None:
        """Positive: 'delay penalty: liquidated damages ... uncapped' must trigger NO-GO."""
        req = EvaluationRequest(
            package_name="ERP Customization Services",
            tender_id="TND-EN-PEN-02",
            dok_pemilihan="Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja.",
            contract_draft=(
                "Penalties and Sanctions:\n"
                "Delay penalty: liquidated damages of 0.2% per day uncapped and without maximum limit."
            ),
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "NO-GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "CON-PENALTY" in gap_ids

    def test_english_penalty_trap_capped_at_five_percent(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: 'liquidated damages ... capped at 5%' must PASS as GO."""
        req = EvaluationRequest(
            package_name="Mobile Banking Maintenance",
            tender_id="TND-EN-PEN-03",
            dok_pemilihan="Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja.",
            contract_draft=(
                "Terms of Agreement:\n"
                "Liquidated damages of 0.1% per day, capped at 5% of total contract value."
            ),
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "CON-PENALTY" not in gap_ids

    def test_english_penalty_trap_maximum_cap(self, engine: EvaluationEngine) -> None:
        """False-positive Trap: 'liquidated damages ... up to a maximum 5%' must PASS as GO."""
        req = EvaluationRequest(
            package_name="Cloud Migration Engineering",
            tender_id="TND-EN-PEN-04",
            dok_pemilihan="Masa penawaran 10 hari kerja, masa sanggah 7 hari kerja.",
            contract_draft=(
                "Remedies for Delay:\n"
                "Liquidated damages of 1/1000 per day up to a maximum 5% of the contract price."
            ),
        )
        res = engine.evaluate(req)
        assert res["verdict"] == "GO"
        gap_ids = [f["id"] for f in res["findings"] if f["status"] == "GAP"]
        assert "CON-PENALTY" not in gap_ids
