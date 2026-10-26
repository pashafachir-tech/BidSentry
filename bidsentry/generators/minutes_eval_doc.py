"""Generate a draft Berita Acara Hasil Evaluasi with evidence rows."""

from __future__ import annotations

import io
from html import escape
from collections.abc import Sequence
from typing import Any

from bidsentry.generators._document_support import DocumentGenerationError, clean_cell, render_pdf, require_docx


def build_minutes_markdown(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
) -> str:
    """Build a portable Markdown BAHE review draft."""

    lines = [
        "# BERITA ACARA HASIL EVALUASI (DRAF)",
        "",
        f"**Paket/Tender:** {_markdown_cell(tender_id)}  ",
        f"**Peserta:** {_markdown_cell(vendor_name)}  ",
        "**Nomor:** [diisi]  ",
        "**Tanggal:** [diisi]",
        "",
        "> Draf ini menyajikan catatan pemeriksaan untuk verifikasi dan pengesahan manusia. Sinyal otomatis bukan keputusan lulus/gugur, kesimpulan pelanggaran, atau penetapan persekongkolan.",
        "",
        "| No. | Temuan | Bukti / halaman | Pemeriksaan | Status review |",
        "| --- | --- | --- | --- | --- |",
    ]
    for index, item in enumerate(findings, 1):
        kind = item.get("anomaly_type") or item.get("signal") or item.get("type") or "Temuan"
        quote = item.get("source_quote") or item.get("verbatim_quote") or "Kutipan tidak tersedia."
        evidence = f"{item.get('page_ref') or 'Tidak tersedia'} — {quote}"
        review = item.get("description") or item.get("interpretation") or "Cocokkan dengan dokumen sumber dan kriteria paket."
        lines.append(
            f"| {index} | {_markdown_cell(kind)} | {_markdown_cell(evidence)} | {_markdown_cell(review)} | [Keputusan reviewer] |"
        )
    if legal_mappings:
        lines.extend(["", "## Rujukan hukum kandidat untuk telaah", ""])
        for item in legal_mappings:
            refs = item.get("candidate_references") or []
            titles = "; ".join(str(ref.get("title") or "") for ref in refs) or "Belum dipetakan"
            lines.append(f"- **{_markdown_cell(item.get('signal') or 'Temuan')}:** {_markdown_cell(titles)}")
            for question in item.get("review_questions", [])[:4]:
                lines.append(f"  - {_markdown_cell(question)}")
    lines.extend([
        "",
        "## Catatan dan kesimpulan Pokja",
        "",
        "[Diisi setelah verifikasi]",
        "",
        "## Anggota Pokja Pemilihan",
        "",
        "1. [Nama / tanda tangan]",
        "2. [Nama / tanda tangan]",
        "3. [Nama / tanda tangan]",
        "",
    ])
    return "\n".join(lines)


def build_minutes_html(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
) -> str:
    """Build an HTML BAHE draft with escaped evidence values."""

    rows: list[str] = []
    for index, item in enumerate(findings, 1):
        kind = item.get("anomaly_type") or item.get("signal") or item.get("type") or "Temuan"
        quote = item.get("source_quote") or item.get("verbatim_quote") or "Kutipan tidak tersedia."
        review = item.get("description") or item.get("interpretation") or "Cocokkan dengan dokumen sumber dan kriteria paket."
        rows.append(
            "<tr>"
            f"<td>{index}</td><td>{escape(clean_cell(kind, 120))}</td>"
            f"<td>{escape(clean_cell(item.get('page_ref') or 'Tidak tersedia', 100))}<br>{escape(clean_cell(quote, 900))}</td>"
            f"<td>{escape(clean_cell(review, 500))}</td><td>[Keputusan reviewer]</td>"
            "</tr>"
        )
    references = []
    for item in legal_mappings:
        refs = item.get("candidate_references") or []
        title_text = "; ".join(clean_cell(ref.get("title"), 220) for ref in refs) or "Belum dipetakan"
        questions = "".join(f"<li>{escape(clean_cell(question, 500))}</li>" for question in item.get("review_questions", [])[:4])
        references.append(f"<li><strong>{escape(clean_cell(item.get('signal') or 'Temuan', 120))}:</strong> {escape(title_text)}<ul>{questions}</ul></li>")
    return (
        "<!doctype html><html lang=\"id\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>BAHE (Draf)</title></head><body>"
        "<h1>BERITA ACARA HASIL EVALUASI (DRAF)</h1>"
        f"<p><strong>Paket/Tender:</strong> {escape(clean_cell(tender_id, 200))}<br>"
        f"<strong>Peserta:</strong> {escape(clean_cell(vendor_name, 240))}<br>"
        "<strong>Nomor:</strong> [diisi] &nbsp; <strong>Tanggal:</strong> [diisi]</p>"
        "<p>Draf ini menyajikan catatan pemeriksaan untuk verifikasi dan pengesahan manusia. Sinyal otomatis bukan keputusan lulus/gugur atau kesimpulan hukum.</p>"
        "<table border=\"1\" cellspacing=\"0\" cellpadding=\"6\"><thead><tr><th>No.</th><th>Temuan</th><th>Bukti / halaman</th><th>Pemeriksaan</th><th>Status review</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        + (f"<h2>Rujukan hukum kandidat untuk telaah</h2><ul>{''.join(references)}</ul>" if references else "")
        + "<h2>Catatan dan kesimpulan Pokja</h2><p>[Diisi setelah verifikasi]</p>"
        "<h2>Anggota Pokja Pemilihan</h2><ol><li>[Nama / tanda tangan]</li><li>[Nama / tanda tangan]</li><li>[Nama / tanda tangan]</li></ol>"
        "</body></html>"
    )


def build_minutes_docx(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
) -> bytes:
    Document = require_docx()
    document = Document()
    document.add_heading("BERITA ACARA HASIL EVALUASI (DRAF)", 0)
    document.add_paragraph(f"Paket/Tender: {clean_cell(tender_id, 200)}")
    document.add_paragraph(f"Peserta: {clean_cell(vendor_name, 240)}")
    document.add_paragraph("Nomor: [diisi]    Tanggal: [diisi]")
    document.add_paragraph(
        "Draf ini menyajikan catatan pemeriksaan berbasis bukti untuk verifikasi dan pengesahan manusia. "
        "Sinyal otomatis bukan keputusan lulus/gugur, kesimpulan pelanggaran, atau penetapan persekongkolan."
    )
    table = document.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    for cell, label in zip(table.rows[0].cells, ("No.", "Temuan", "Bukti / halaman", "Pemeriksaan", "Status review")):
        cell.text = label
    for index, item in enumerate(findings, 1):
        row = table.add_row().cells
        row[0].text = str(index)
        row[1].text = clean_cell(item.get("anomaly_type") or item.get("signal") or item.get("type") or "Temuan", 120)
        row[2].text = f"{clean_cell(item.get('page_ref') or 'Tidak tersedia', 100)}\n{clean_cell(item.get('source_quote') or item.get('verbatim_quote') or 'Kutipan tidak tersedia.', 900)}"
        row[3].text = clean_cell(item.get("description") or item.get("interpretation") or "Cocokkan dengan dokumen sumber dan kriteria paket.", 500)
        row[4].text = "[Keputusan reviewer]"
    if legal_mappings:
        document.add_heading("Rujukan hukum kandidat untuk telaah", level=1)
        for item in legal_mappings:
            refs = item.get("candidate_references") or []
            ref_names = "; ".join(clean_cell(ref.get("title"), 220) for ref in refs) or "Belum dipetakan"
            document.add_paragraph(f"{clean_cell(item.get('signal'), 120)}: {ref_names}")
            for question in item.get("review_questions", [])[:4]:
                document.add_paragraph(clean_cell(question, 500), style="List Bullet")
    document.add_paragraph("Catatan dan kesimpulan Pokja: [diisi setelah verifikasi]")
    document.add_paragraph("Anggota Pokja Pemilihan:\n1. [Nama / tanda tangan]\n2. [Nama / tanda tangan]\n3. [Nama / tanda tangan]")
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


def build_minutes_pdf(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
) -> bytes:
    rows = [["No.", "Temuan", "Bukti / halaman", "Pemeriksaan", "Status review"]]
    for index, item in enumerate(findings, 1):
        rows.append([
            str(index),
            clean_cell(item.get("anomaly_type") or item.get("signal") or item.get("type") or "Temuan", 120),
            f"{clean_cell(item.get('page_ref') or 'Tidak tersedia', 100)}\n{clean_cell(item.get('source_quote') or item.get('verbatim_quote') or 'Kutipan tidak tersedia.', 900)}",
            clean_cell(item.get("description") or item.get("interpretation") or "Cocokkan dengan dokumen sumber dan kriteria paket.", 500),
            "[Keputusan reviewer]",
        ])
    paragraphs = [
        f"Paket/Tender: {clean_cell(tender_id, 200)}",
        f"Peserta: {clean_cell(vendor_name, 240)}",
        "Nomor: [diisi]    Tanggal: [diisi]",
        "Draf untuk verifikasi dan pengesahan manusia. Sinyal otomatis bukan keputusan lulus/gugur atau kesimpulan hukum.",
        "Rujukan kandidat: " + ("; ".join(clean_cell(ref.get("title"), 220) for item in legal_mappings for ref in item.get("candidate_references", [])) or "Belum dipetakan."),
        "Catatan dan kesimpulan Pokja: [diisi setelah verifikasi]",
        "Anggota Pokja Pemilihan: [Nama / tanda tangan]",
    ]
    return render_pdf("BERITA ACARA HASIL EVALUASI (DRAF)", paragraphs, [rows])


def write_minutes_docx(path: str, tender_id: str, vendor_name: str, findings: Sequence[dict[str, Any]], legal_mappings: Sequence[dict[str, Any]] = ()) -> str:
    content = build_minutes_docx(tender_id, vendor_name, findings, legal_mappings)
    try:
        with open(path, "wb") as stream:
            stream.write(content)
    except OSError as exc:
        raise DocumentGenerationError("BAHE draft could not be saved to the requested path.") from exc
    return path


def _markdown_cell(value: Any) -> str:
    text = clean_cell(value, 1000)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("`", "\\`").replace("\n", " ")
