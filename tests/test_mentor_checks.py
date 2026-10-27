from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from docx import Document

from bidsentry.audits.penalty_calculator import calculate_penalty_scenarios
from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest
from bidsentry.evaluators.grounded_checker import verify_grounded_citation
from bidsentry.forensics.adendum_diff import diff_addendum
from bidsentry.generators.sanggahan_builder import build_sanggahan_docx, build_sanggahan_markdown


ROOT = Path(__file__).resolve().parents[1]


def test_supported_quotation_must_be_an_exact_source_substring() -> None:
    text = "Status pajak sesuai bukti resmi."
    assert verify_grounded_citation(text, "pajak sesuai") == (True, 1.0)
    assert verify_grounded_citation(text, "status pajak berlaku") == (False, 0.0)
    assert verify_grounded_citation(text, None) == (False, 0.0)


def test_public_lpse_kswp_wording_is_detected_without_claiming_validation() -> None:
    source = "Mempunyai status valid keterangan Wajib Pajak berdasarkan hasil Konfirmasi Status Wajib Pajak."
    result = EvaluationEngine().evaluate(EvaluationRequest(dok_pemilihan=source))
    finding = next(item for item in result["findings"] if item["id"] == "ADM-KSWP")
    assert finding["status"] == "REVIEW"
    assert "belum diverifikasi" in finding["review_note"]


def test_uncapped_penalty_exposes_contract_excess_over_illustrative_cap() -> None:
    clause = "Denda keterlambatan sebesar 2/1000 dari nilai kontrak setiap hari keterlambatan."
    result = EvaluationEngine().evaluate(EvaluationRequest(
        contract_value_idr=1_000_000_000,
        contract_draft=clause,
    ))
    penalty = result["penalty_simulation"]
    assert penalty["uncapped_clause_detected"] is True
    assert "CRITICAL_POISON_PILL" in penalty["alerts"]
    assert [row["delay_days"] for row in penalty["scenarios"]] == [10, 30, 50]
    assert [row["contract_clause_amount_idr"] for row in penalty["scenarios"]] == [20_000_000, 60_000_000, 100_000_000]
    assert result["executive_summary"]["potential_financial_exposure_idr"] == 50_000_000
    assert penalty["assumptions"]["illustrative_cap_percentage"] == 0.05


def test_addendum_marks_modified_and_removed_requirements() -> None:
    result = diff_addendum(
        "Peserta wajib memiliki SBU BG002 yang berlaku.\nPenawaran berlaku 90 hari.",
        "Peserta wajib memiliki SBU BG002 yang berlaku minimal 30 hari.",
    )
    assert result["counts"]["MODIFIED"] == 1
    assert result["counts"]["REVOKED"] == 1
    changed = next(row for row in result["changes"] if row["change_status"] == "MODIFIED")
    assert changed["original_requirement"] and changed["adendum_requirement"]


def test_sanggahan_docx_contains_verified_quote_and_candidate_law_references() -> None:
    quote = "SBU BG002 dipersyaratkan untuk paket ini."
    findings = [{"category": "Administrasi", "clause": "SBU", "requirement_evidence": quote}]
    draft = build_sanggahan_markdown(
        tender_id="LPSE-TEST", package_name="Paket uji", company_name="Penyedia uji",
        notice_number="", pokja_name="", source_text=quote, findings=findings,
    )
    docx = build_sanggahan_docx(
        tender_id="LPSE-TEST", package_name="Paket uji", company_name="Penyedia uji",
        notice_number="", pokja_name="", source_text=quote, findings=findings,
    )
    docx_text = "\n".join(paragraph.text for paragraph in Document(BytesIO(docx)).paragraphs)
    assert quote in draft and quote in docx_text
    assert "Perpres 16/2018" in draft and "Pasal 6" in draft
    assert "tidak menyatakan bahwa suatu pelanggaran telah terjadi" in draft


def test_sanggahan_only_adds_competition_law_candidate_for_relevant_signal() -> None:
    quote = "Peserta terkait dengan penyedia lain."
    draft = build_sanggahan_markdown(
        tender_id="LPSE-TEST", package_name="Paket uji", company_name="Penyedia uji",
        notice_number="", pokja_name="", source_text=quote,
        findings=[{"category": "Kolusi", "requirement_evidence": quote}],
    )
    assert "UU 5/1999, Pasal 22" in draft
    assert "bukan kesimpulan pelanggaran" in draft


def test_langflow_export_is_valid_json_with_connected_chat_model_path() -> None:
    flow = json.loads((ROOT / "langflow" / "tender_extraction_flow.json").read_text(encoding="utf-8"))
    nodes = flow["data"]["nodes"]
    edges = flow["data"]["edges"]
    ids = {node["id"] for node in nodes}
    assert len(ids) == len(nodes)
    assert all(edge["source"] in ids and edge["target"] in ids for edge in edges)
    assert any(node.get("data", {}).get("type") == "LanguageModelComponent" for node in nodes)
    assert len(edges) >= 3


def test_langflow_prompt_escapes_literal_json_braces() -> None:
    flow = json.loads((ROOT / "langflow" / "tender_extraction_flow.json").read_text(encoding="utf-8"))
    prompt_node = next(node for node in flow["data"]["nodes"] if node.get("data", {}).get("type") == "Prompt")
    prompt = prompt_node["data"]["node"]["template"]["template"]["value"]

    rendered = prompt.format()

    assert '{{"scope"' in prompt
    assert '{"scope": string or null' in rendered
    assert "{{" not in rendered


def test_brand_lockin_detection_flags_exclusive_hardware_specifications() -> None:
    text = "Prosesor per Node: 2 x Intel Xeon Scalable Gen 5 (Emerald Rapids), mendukung UPI 4.0. GPU: NVIDIA H100 SXM5."
    result = EvaluationEngine().evaluate(EvaluationRequest(dok_pemilihan=text))
    finding_ids = {f["id"] for f in result["findings"]}
    assert "SPEC-LOCKIN-CPU" in finding_ids
    assert "SPEC-LOCKIN-GPU" in finding_ids
    cpu_finding = next(f for f in result["findings"] if f["id"] == "SPEC-LOCKIN-CPU")
    assert cpu_finding["status"] == "GAP"
    assert cpu_finding["severity"] == "HIGH"
    assert "Pasal 19 ayat (1) Perpres 12/2021" in cpu_finding["review_note"]


def test_compressed_procurement_timeline_flags_short_bidding_and_objection_periods() -> None:
    text = "Masa penyusunan dokumen penawaran: 3 hari kerja. Masa sanggah: 3 hari kerja."
    result = EvaluationEngine().evaluate(EvaluationRequest(dok_pemilihan=text))
    finding = next(f for f in result["findings"] if f["id"] == "PROC-TIMELINE-COMPRESSED")
    assert finding["status"] == "GAP"
    assert finding["severity"] == "HIGH"
    assert "Pasal 54 Perpres 12/2021" in finding["review_note"]
    assert "7 hari kerja" in finding["review_note"]
    assert "5 hari kerja" in finding["review_note"]
    assert result["verdict"] == "NO-GO"


def test_deepseek_erp_financial_fatal_flaws_detection() -> None:
    text = (
        "Pagu Anggaran : Rp 8.500.000.000,-\n"
        "TOTAL BIAYA (A + B) : 10.160.000.000\n"
        "SELISIH (OVER BUDGET) : (1.660.000.000)\n"
        "1. Mark-up Tarif Man-Month: Tarif Solution Architect sebesar Rp 150.000.000/man-month dan Project Manager Rp 120.000.000/man-month berada ±250–300% di atas standar rata-rata industri nasional (IKINDO) yang berkisar Rp 40.000.000–Rp 60.000.000/man-month.\n"
        "2. Duplikasi Lisensi: Pos 'Lisensi Core ERP — Tahun Pertama' (Rp 1.200.000.000) dan Pos 'Biaya Pemeliharaan Berkala (Tahun Pertama)' (Rp 480.000.000) berpotensi tumpang tindih (double counting), karena biaya pemeliharaan tahun pertama umumnya sudah mencakup hak penggunaan lisensi.\n"
        "Kualifikasi Personel: Project Manager (PMP / PRINCE2), Solution Architect (TOGAF / ERP Architect), sertifikasi modul ERP.\n"
    )
    result = EvaluationEngine().evaluate(EvaluationRequest(package_name="Implementasi ERP", dok_pemilihan=text))
    finding_ids = {f["id"] for f in result["findings"]}

    assert "FIN-OVER-BUDGET" in finding_ids
    assert "FIN-MARKUP-RATE" in finding_ids
    assert "FIN-DOUBLE-LICENSE" in finding_ids
    assert "ADM-EXPERTS" in finding_ids

    over_budget = next(f for f in result["findings"] if f["id"] == "FIN-OVER-BUDGET")
    assert over_budget["status"] == "GAP"
    assert over_budget["severity"] == "HIGH"
    assert "10.160.000.000" in over_budget["review_note"]
    assert "8.500.000.000" in over_budget["review_note"]

    markup = next(f for f in result["findings"] if f["id"] == "FIN-MARKUP-RATE")
    assert markup["status"] == "GAP"
    assert markup["severity"] == "HIGH"
    assert "150.000.000" in markup["review_note"]
    assert "INKINDO" in markup["review_note"]

    double_lic = next(f for f in result["findings"] if f["id"] == "FIN-DOUBLE-LICENSE")
    assert double_lic["status"] == "GAP"
    assert double_lic["severity"] == "HIGH"
    assert "1.200.000.000" in double_lic["review_note"]
    assert "double counting" in double_lic["review_note"]

    experts = next(f for f in result["findings"] if f["id"] == "ADM-EXPERTS")
    assert experts["status"] == "REVIEW"
    assert experts["severity"] == "MEDIUM"

    assert result["verdict"] == "NO-GO"
    assert result["risk_level"] == "CRITICAL"
    assert result["risk_score"] >= 70
