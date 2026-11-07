"""Generate a draft Berita Acara Hasil Evaluasi (BAHE) with evidence rows.

Rows come from :func:`normalize_finding`, so engine findings (``clause`` /
``requirement_evidence``) and forensic anomalies (``anomaly_type`` /
``source_quote``) both render with their real title, quote and status.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from html import escape
from typing import Any

from bidsentry.generators._document_support import DocumentGenerationError, clean_cell, normalize_finding, render_pdf, require_docx

_DISCLAIMER = (
    "Draf ini menyajikan catatan pemeriksaan berbasis bukti untuk verifikasi dan pengesahan manusia. "
    "Sinyal otomatis bukan keputusan lulus/gugur, kesimpulan pelanggaran, atau penetapan persekongkolan."
)
_HEADERS = ("No.", "Kode / temuan", "Status", "Bukti / lokasi", "Catatan pemeriksaan", "Keputusan Pokja")


def _rows(findings: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    return [normalize_finding(item) for item in findings if isinstance(item, dict)]


def _risk_line(risk: dict[str, Any] | None) -> str | None:
    if not risk or not risk.get("label"):
        return None
    return f"Tingkat risiko sistem: {clean_cell(risk.get('label'), 40)} (aturan {clean_cell(risk.get('rule_applied'), 8)}). {clean_cell(risk.get('rationale'), 400)}"


def _meta_lines(tender_id: str, vendor_name: str, meta: dict[str, Any] | None) -> list[str]:
    meta = meta or {}
    lines = [f"Paket/Tender: {clean_cell(meta.get('package_name') or tender_id, 240)}"]
    if meta.get("package_name") and tender_id:
        lines.append(f"Kode tender: {clean_cell(tender_id, 200)}")
    if meta.get("pokja_name"):
        lines.append(f"Pokja: {clean_cell(meta['pokja_name'], 240)}")
    lines.append(f"Peserta: {clean_cell(vendor_name, 240)}")
    if meta.get("audit_id"):
        lines.append(f"ID audit BidSentry: {clean_cell(meta['audit_id'], 80)}")
    lines.append("Nomor: [diisi]    Tanggal: [diisi]")
    return lines


def build_minutes_markdown(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
    *,
    risk: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> str:
    """Build a portable Markdown BAHE review draft."""
    lines = ["# BERITA ACARA HASIL EVALUASI (DRAF)", ""]
    lines += [f"**{line.split(':', 1)[0]}:**{line.split(':', 1)[1]}  " for line in _meta_lines(tender_id, vendor_name, meta)]
    lines += ["", f"> {_DISCLAIMER}", ""]
    if (risk_text := _risk_line(risk)):
        lines += [f"**{risk_text}**", ""]
    lines += ["| " + " | ".join(_HEADERS) + " |", "| " + " | ".join("---" for _ in _HEADERS) + " |"]
    for index, row in enumerate(_rows(findings), 1):
        lines.append(
            f"| {index} | {_markdown_cell(row['code'] + ' — ' + row['title'])} | {_markdown_cell(row['status_label'])} | "
            f"{_markdown_cell(row['locator'] + ' — ' + row['quote'])} | {_markdown_cell(row['note'])} | {_markdown_cell(row['reviewer'])} |"
        )
    references = [row for row in _rows(findings) if row["legal_reference"]]
    if references or legal_mappings:
        lines += ["", "## Rujukan hukum kandidat (perlu verifikasi hukum)", ""]
        for row in references:
            lines.append(f"- **{_markdown_cell(row['code'])}:** {_markdown_cell(row['legal_reference'])}")
        for item in legal_mappings:
            refs = item.get("candidate_references") or []
            titles = "; ".join(str(ref.get("title") or "") for ref in refs) or "Belum dipetakan"
            lines.append(f"- **{_markdown_cell(item.get('signal') or 'Temuan')}:** {_markdown_cell(titles)}")
            for question in item.get("review_questions", [])[:4]:
                lines.append(f"  - {_markdown_cell(question)}")
    lines += [
        "", "## Catatan dan kesimpulan Pokja", "", "[Diisi setelah verifikasi]", "",
        "## Anggota Pokja Pemilihan", "", "1. [Nama / tanda tangan]", "2. [Nama / tanda tangan]", "3. [Nama / tanda tangan]", "",
    ]
    return "\n".join(lines)


def build_minutes_html(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
    *,
    risk: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> str:
    """Build an HTML BAHE draft with escaped evidence values."""
    body_rows = "".join(
        "<tr>"
        f"<td>{index}</td><td><strong>{escape(row['code'])}</strong><br>{escape(row['title'])}</td><td>{escape(row['status_label'])}</td>"
        f"<td>{escape(row['locator'])}<br>{escape(row['quote'])}</td><td>{escape(row['note'])}</td><td>{escape(row['reviewer'])}</td>"
        "</tr>"
        for index, row in enumerate(_rows(findings), 1)
    )
    references = "".join(f"<li><strong>{escape(row['code'])}:</strong> {escape(row['legal_reference'])}</li>" for row in _rows(findings) if row["legal_reference"])
    for item in legal_mappings:
        refs = item.get("candidate_references") or []
        title_text = "; ".join(clean_cell(ref.get("title"), 220) for ref in refs) or "Belum dipetakan"
        questions = "".join(f"<li>{escape(clean_cell(question, 500))}</li>" for question in item.get("review_questions", [])[:4])
        references += f"<li><strong>{escape(clean_cell(item.get('signal') or 'Temuan', 120))}:</strong> {escape(title_text)}<ul>{questions}</ul></li>"
    meta_html = "<br>".join(escape(line) for line in _meta_lines(tender_id, vendor_name, meta))
    risk_html = f"<p><strong>{escape(text)}</strong></p>" if (text := _risk_line(risk)) else ""
    return (
        "<!doctype html><html lang=\"id\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>BAHE (Draf)</title></head><body>"
        f"<h1>BERITA ACARA HASIL EVALUASI (DRAF)</h1><p>{meta_html}</p><p>{escape(_DISCLAIMER)}</p>{risk_html}"
        "<table border=\"1\" cellspacing=\"0\" cellpadding=\"6\"><thead><tr>" + "".join(f"<th>{escape(h)}</th>" for h in _HEADERS) + "</tr></thead>"
        f"<tbody>{body_rows}</tbody></table>"
        + (f"<h2>Rujukan hukum kandidat (perlu verifikasi hukum)</h2><ul>{references}</ul>" if references else "")
        + "<h2>Catatan dan kesimpulan Pokja</h2><p>[Diisi setelah verifikasi]</p>"
        "<h2>Anggota Pokja Pemilihan</h2><ol><li>[Nama / tanda tangan]</li><li>[Nama / tanda tangan]</li><li>[Nama / tanda tangan]</li></ol>"
        "</body></html>"
    )


def build_minutes_docx(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
    *,
    risk: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> bytes:
    Document = require_docx()
    document = Document()
    document.add_heading("BERITA ACARA HASIL EVALUASI (DRAF)", 0)
    for line in _meta_lines(tender_id, vendor_name, meta):
        document.add_paragraph(line)
    document.add_paragraph(_DISCLAIMER)
    if (risk_text := _risk_line(risk)):
        document.add_paragraph().add_run(risk_text).bold = True
    table = document.add_table(rows=1, cols=len(_HEADERS))
    table.style = "Table Grid"
    for cell, label in zip(table.rows[0].cells, _HEADERS):
        cell.text = label
    for index, row in enumerate(_rows(findings), 1):
        cells = table.add_row().cells
        cells[0].text = str(index)
        cells[1].text = f"{row['code']}\n{row['title']}"
        cells[2].text = row["status_label"]
        cells[3].text = f"{row['locator']}\n{row['quote']}"
        cells[4].text = row["note"]
        cells[5].text = row["reviewer"]
    references = [row for row in _rows(findings) if row["legal_reference"]]
    if references or legal_mappings:
        document.add_heading("Rujukan hukum kandidat (perlu verifikasi hukum)", level=1)
        for row in references:
            document.add_paragraph(f"{row['code']}: {row['legal_reference']}", style="List Bullet")
        for item in legal_mappings:
            refs = item.get("candidate_references") or []
            ref_names = "; ".join(clean_cell(ref.get("title"), 220) for ref in refs) or "Belum dipetakan"
            document.add_paragraph(f"{clean_cell(item.get('signal'), 120)}: {ref_names}")
            for question in item.get("review_questions", [])[:4]:
                document.add_paragraph(clean_cell(question, 500), style="List Bullet")
    document.add_heading("Catatan dan kesimpulan Pokja", level=1)
    document.add_paragraph("[Diisi setelah verifikasi]")
    document.add_heading("Anggota Pokja Pemilihan", level=1)
    for number in range(1, 4):
        document.add_paragraph(f"{number}. [Nama / tanda tangan]")
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


def build_minutes_pdf(
    tender_id: str,
    vendor_name: str,
    findings: Sequence[dict[str, Any]],
    legal_mappings: Sequence[dict[str, Any]] = (),
    *,
    risk: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> bytes:
    rows = [list(_HEADERS)]
    for index, row in enumerate(_rows(findings), 1):
        rows.append([str(index), f"{row['code']}\n{row['title']}", row["status_label"], f"{row['locator']}\n{row['quote']}", row["note"], row["reviewer"]])
    paragraphs = [*_meta_lines(tender_id, vendor_name, meta), _DISCLAIMER]
    if (risk_text := _risk_line(risk)):
        paragraphs.append(risk_text)
    paragraphs += [
        "Rujukan kandidat (perlu verifikasi hukum): " + ("; ".join(f"{row['code']}: {row['legal_reference']}" for row in _rows(findings) if row["legal_reference"]) or "Belum dipetakan."),
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
