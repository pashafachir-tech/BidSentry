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
