"""Build an editable bidder objection draft from verified source quotations."""

from __future__ import annotations

import io
from html import escape
from typing import Any

from bidsentry.generators._document_support import DocumentGenerationError, clean_cell, render_pdf, require_docx


def _eligible(items: list[dict[str, Any]], source_text: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        category = str(item.get("issue_type", item.get("category", ""))).casefold()
        if not any(word in category for word in ("diskrimin", "persaingan", "kolusi", "anti-kompetitif", "administrasi", "adendum", "kualifikasi")):
            continue
        quote = item.get("verbatim_quote") or item.get("requirement_evidence") or item.get("source_quote")
        if isinstance(quote, str) and quote.strip() and quote in source_text:
            output.append({**item, "verbatim_quote": quote})
    return output


def _candidate_legal_citations(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not items:
        return []
    citations = [{
        "reference": "Perpres 16/2018 sebagaimana diubah dengan Perpres 12/2021 dan Perpres 46/2025, Pasal 6 (prinsip pengadaan)",
        "provision": "Rujukan awal untuk ditelaah terhadap fakta dan dokumen paket; kutipan ini tidak menyatakan bahwa suatu pelanggaran telah terjadi. Naskah konsolidasi LKPP: https://jdih.lkpp.go.id/regulation/konsolidasi/konsolidasi-nomor-46-tahun-2025",
    }]
    collusion_signal = any(
        any(word in str(item.get("issue_type", item.get("category", ""))).casefold() for word in ("kolusi", "persekongkol", "persaingan", "kartel"))
        for item in items
    )
    if collusion_signal:
        citations.append({
            "reference": "UU 5/1999, Pasal 22 (persekongkolan tender)",
            "provision": "Cantumkan hanya jika fakta pendukung dan unsur pasal ditelaah secara terpisah. Kemiripan dokumen atau hubungan entitas saja bukan kesimpulan pelanggaran. Naskah: https://peraturan.bpk.go.id/Details/45280/uu-no-5-tahun-1999",
        })
    return citations


def build_sanggahan_markdown(
    *, tender_id: str, package_name: str, company_name: str, notice_number: str,
    pokja_name: str, source_text: str, findings: list[dict[str, Any]],
    legal_citations: list[dict[str, str]] | None = None,
) -> str:
    """Return a formal draft; only exact, source-verified quotes are included."""
    eligible = _eligible(findings, source_text)
    rows: list[str] = [
        "# SURAT SANGGAHAN / PERMOHONAN PENJELASAN", "",
        "Nomor: [diisi]  ", "Lampiran: [diisi]  ", "Perihal: Sanggahan dan permohonan penjelasan atas dokumen pemilihan", "",
        "Kepada Yth.  ", f"Pokja Pemilihan {pokja_name or '[nama Pokja/instansi]'}  ", "di tempat", "",
        "Dengan hormat,", "",
        f"Kami, {company_name or '[nama perusahaan]'}, peserta pada paket {package_name or '[nama paket]'} (nomor tender {tender_id or '[nomor tender]'}; pengumuman {notice_number or '[nomor pengumuman]'}), menyampaikan sanggahan/permohonan penjelasan berikut untuk ditelaah sesuai dokumen dan jadwal resmi.", "",
    ]
    if eligible:
        for index, item in enumerate(eligible, 1):
            title = clean_cell(item.get("clause") or item.get("category") or item.get("id") or "Ketentuan yang dipersoalkan", 240)
            quote = clean_cell(item["verbatim_quote"], 1200)
            locator = clean_cell(item.get("source") or item.get("page_ref") or "Lokator tidak tercantum", 200)
            concern = clean_cell(item.get("objection_reason") or item.get("review_note") or item.get("evidence") or "Mohon penjelasan atas dasar dan penerapan ketentuan ini.", 1000)
            rows.extend([f"## {index}. {title}", "", f"> {quote}", "", f"Sumber: {locator}", "", f"Hal yang dimohonkan penjelasan: {concern}", "", "Mohon Pokja menjelaskan dasar, penerapan yang sama kepada seluruh peserta, dan dokumen/ketentuan yang menjadi rujukan.", ""])
    else:
        rows.extend(["Belum ada temuan dengan kutipan persis dari dokumen sumber yang dapat dimasukkan. Lengkapi temuan dan dokumen sumber sebelum membuat surat.", ""])
    citations = _candidate_legal_citations(eligible) + (legal_citations or [])
    if citations:
        rows.extend(["## Rujukan awal untuk diverifikasi reviewer", ""])
        for citation in citations:
            reference = clean_cell(citation.get("reference", ""), 240)
            clause = clean_cell(citation.get("provision", ""), 800)
            if reference:
                rows.append(f"- {reference}{': ' + clause if clause else ''}")
        rows.append("")
    rows.extend([
        "Permohonan ini didasarkan pada salinan dokumen yang tersedia kepada kami. Mohon konfirmasi versi yang berlaku, nomor halaman, jadwal, serta kanal penyampaian sanggahan sebelum surat digunakan.", "",
        "Demikian kami sampaikan. Atas perhatian dan penjelasan Pokja, kami ucapkan terima kasih.", "",
        "Hormat kami,", "", "[Nama dan jabatan penandatangan]", company_name or "[Nama perusahaan]", "", "DRAF UNTUK DITINJAU: periksa kelayakan prosedural, tenggat, fakta, kutipan, dasar hukum, kewenangan, dan tanda tangan sebelum diajukan.", "",
    ])
    return "\n".join(rows)


def build_sanggahan_docx(**kwargs: Any) -> bytes:
    markdown = build_sanggahan_markdown(**kwargs)
    Document = require_docx()
    doc = Document()
    for line in markdown.splitlines():
        if line.startswith("# "):
            doc.add_heading(line[2:], 0)
        elif line.startswith("## "):
            doc.add_heading(line[3:], 2)
        elif line.startswith("> "):
            paragraph = doc.add_paragraph()
            paragraph.style = "Quote"
            paragraph.add_run(line[2:])
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif line:
            doc.add_paragraph(line)
    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


def build_sanggahan_html(**kwargs: Any) -> str:
    markdown = build_sanggahan_markdown(**kwargs)
    paragraphs = "".join(f"<p>{escape(line[2:] if line.startswith(('> ', '# ', '- ')) else line)}</p>" for line in markdown.splitlines() if line)
    return "<!doctype html><html lang=\"id\"><meta charset=\"utf-8\"><title>Draf sanggahan</title><body>" + paragraphs + "</body></html>"


def build_sanggahan_pdf(**kwargs: Any) -> bytes:
    markdown = build_sanggahan_markdown(**kwargs)
    return render_pdf("SURAT SANGGAHAN / PERMOHONAN PENJELASAN", [line.removeprefix("# ").removeprefix("> ") for line in markdown.splitlines() if line], None)
