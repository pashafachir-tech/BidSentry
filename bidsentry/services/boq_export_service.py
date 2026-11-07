"""Excel BoQ workbook with live formulas, cross-checked against the Python calculator.

The workbook is designed for the demo question "show me the calculator":

* ``BoQ``            – one row per parsed line item. *Jumlah hitung* and
                       *Selisih* are Excel formulas (``=Volume*Harga``) so the
                       reviewer can audit them in Excel; the *Cek Python*
                       column is the independent result of
                       :func:`bidsentry.audits.financial.audit_boq`.
* ``Ringkasan``      – totals as formulas, plus pagu/HPS read by the engine.
* ``Jejak Hitungan`` – every calculation step of the audit proof log.
"""

from __future__ import annotations

import base64
import io
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from bidsentry.audits.financial import audit_boq, parse_boq_text
from bidsentry.schemas.comprehensive import BoQLineItem

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_IDR_FORMAT = '#,##0;[Red]-#,##0'


class BoQExportService:
    def create(self, audit: dict[str, Any], source_text: str, *, role: str | None = None) -> dict[str, Any]:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        items: list[BoQLineItem] = parse_boq_text(source_text or "")
        python_check = audit_boq(items)
        line_checks = python_check.get("line_item_checks", [])

        workbook = Workbook()
        header_fill = PatternFill("solid", fgColor="1F3A2E")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        warn_fill = PatternFill("solid", fgColor="FDE2E1")
        wrap = Alignment(wrap_text=True, vertical="top")

        # ---------------------------------------------------------------- BoQ
        sheet = workbook.active
        sheet.title = "BoQ"
        meta_rows = [
            ("Paket", audit.get("package_name") or "—"),
            ("Kode tender", audit.get("tender_id") or "—"),
            ("ID audit", audit.get("audit_id") or "—"),
            ("Diunduh oleh peran", {"pokja": "Pokja Pemilihan", "vendor": "Penyedia / Vendor"}.get(role or "", role or "—")),
            ("Dibuat", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("Tingkat risiko audit", (audit.get("risk") or {}).get("label") or audit.get("risk_level") or "—"),
        ]
        for row_index, (label, value) in enumerate(meta_rows, start=1):
            sheet.cell(row=row_index, column=1, value=label).font = Font(bold=True, size=12)
            sheet.cell(row=row_index, column=2, value=str(value)).font = Font(size=12)
        headers = ["No", "Uraian", "Volume", "Satuan", "Harga Satuan (Rp)", "Jumlah Tertulis (Rp)", "Jumlah Hitung (Rp)", "Selisih (Rp)", "Status Excel", "Cek Python", "HPS Satuan (Rp)", "Rasio thd HPS", "Kutipan sumber"]
        header_row = len(meta_rows) + 2
        for column, title in enumerate(headers, start=1):
            cell = sheet.cell(row=header_row, column=column, value=title)
            cell.fill, cell.font, cell.alignment = header_fill, header_font, Alignment(wrap_text=True, vertical="center")
        first_data_row = header_row + 1
        for offset, item in enumerate(items):
            r = first_data_row + offset
            check = line_checks[offset] if offset < len(line_checks) else {}
            values: list[Any] = [
                offset + 1, item.description, float(item.volume), item.unit, float(item.unit_price_offered), float(item.total_offered),
                f"=C{r}*E{r}", f"=F{r}-G{r}", f'=IF(ABS(H{r})>1,"SELISIH","SESUAI")',
                "SELISIH" if check.get("math_status") == "MATH_MISMATCH" else "SESUAI",
                float(item.hps_unit_price) if item.hps_unit_price is not None else None,
                f'=IF(AND(ISNUMBER(K{r}),K{r}>0),E{r}/K{r},"")',
                item.source_quote or "",
            ]
            for column, value in enumerate(values, start=1):
                cell = sheet.cell(row=r, column=column, value=value)
                cell.font = Font(size=12)
                if column in (5, 6, 7, 8, 11):
                    cell.number_format = _IDR_FORMAT
                if column == 12:
                    cell.number_format = "0.00%"
                if column in (2, 13):
                    cell.alignment = wrap
            if check.get("math_status") == "MATH_MISMATCH":
                for column in range(1, len(headers) + 1):
                    sheet.cell(row=r, column=column).fill = warn_fill
        last_data_row = first_data_row + max(len(items), 1) - 1
        total_row = last_data_row + 1
        if items:
            sheet.cell(row=total_row, column=2, value="TOTAL").font = Font(bold=True, size=12)
            for column_letter in ("F", "G", "H"):
                cell = sheet[f"{column_letter}{total_row}"]
                cell.value = f"=SUM({column_letter}{first_data_row}:{column_letter}{last_data_row})"
                cell.number_format, cell.font = _IDR_FORMAT, Font(bold=True, size=12)
        else:
            sheet.cell(row=first_data_row, column=2, value="Tidak ada baris BoQ terstruktur yang terbaca. Format yang didukung: 'Uraian | 10 unit | Rp harga | Rp jumlah | Rp HPS satuan'.").alignment = wrap
        widths = [6, 42, 10, 10, 18, 20, 20, 16, 14, 13, 18, 13, 60]
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width
        sheet.freeze_panes = sheet.cell(row=first_data_row, column=3)

        # ---------------------------------------------------------- Ringkasan
        summary = workbook.create_sheet("Ringkasan")
        over_budget = next((step for step in audit.get("proof_log", []) if step.get("inputs", {}).get("rule") == "FIN-OVER-BUDGET"), None)
        pagu = (over_budget or {}).get("inputs", {}).get("pagu_idr")
        boq_total_stated = (over_budget or {}).get("inputs", {}).get("total_boq_idr")
        mismatches = sum(1 for check in line_checks if check.get("math_status") == "MATH_MISMATCH")
        summary_rows: list[tuple[str, Any, str | None]] = [
            ("Jumlah baris BoQ", len(items), None),
            ("Total tertulis (Rp)", f"=BoQ!F{total_row}" if items else 0, _IDR_FORMAT),
            ("Total hasil hitung (Rp)", f"=BoQ!G{total_row}" if items else 0, _IDR_FORMAT),
            ("Selisih total (Rp)", f"=BoQ!H{total_row}" if items else 0, _IDR_FORMAT),
            ("Baris selisih (formula Excel)", f'=COUNTIF(BoQ!I{first_data_row}:I{last_data_row},"SELISIH")' if items else 0, None),
            ("Baris selisih (kalkulator Python)", mismatches, None),
            ("Pagu anggaran terbaca (Rp)", pagu if pagu is not None else "tidak terbaca", _IDR_FORMAT if pagu is not None else None),
            ("Total BoQ/HPS tertulis di dokumen (Rp)", boq_total_stated if boq_total_stated is not None else "tidak terbaca", _IDR_FORMAT if boq_total_stated is not None else None),
            ("Selisih terhadap pagu (Rp)", "=B9-B8" if pagu is not None and boq_total_stated is not None else "—", _IDR_FORMAT),
        ]
        summary.cell(row=1, column=1, value="Ringkasan perhitungan BoQ").font = Font(bold=True, size=14)
        for index, (label, value, number_format) in enumerate(summary_rows, start=2):
            summary.cell(row=index, column=1, value=label).font = Font(size=12)
            cell = summary.cell(row=index, column=2, value=value)
            cell.font = Font(size=12, bold=True)
            if number_format:
                cell.number_format = number_format
        summary.cell(row=len(summary_rows) + 3, column=1, value=python_check.get("interpretation", "")).alignment = wrap
        summary.column_dimensions["A"].width = 42
        summary.column_dimensions["B"].width = 26

        # ----------------------------------------------------- Jejak Hitungan
        trace = workbook.create_sheet("Jejak Hitungan")
        trace_headers = ["Langkah", "Jenis", "Judul", "Pelaksana", "Rumus / aturan", "Input", "Output"]
        for column, title in enumerate(trace_headers, start=1):
            cell = trace.cell(row=1, column=column, value=title)
            cell.fill, cell.font = header_fill, header_font
        for row_index, step in enumerate(audit.get("proof_log", []), start=2):
            values = [step.get("step_id"), step.get("kind"), step.get("title"), step.get("actor"), step.get("formula") or "", json.dumps(step.get("inputs", {}), ensure_ascii=False, default=str), json.dumps(step.get("outputs", {}), ensure_ascii=False, default=str)]
            for column, value in enumerate(values, start=1):
                cell = trace.cell(row=row_index, column=column, value=value)
                cell.alignment, cell.font = wrap, Font(size=11)
        for letter, width in zip("ABCDEFG", (9, 14, 40, 30, 50, 60, 60)):
            trace.column_dimensions[letter].width = width

        stream = io.BytesIO()
        workbook.save(stream)
        package = (audit.get("tender_id") or audit.get("audit_id") or "audit").replace(" ", "-")[:40]
        return {
            "filename": f"bidsentry-boq-{package}.xlsx",
            "content_type": XLSX_MIME,
            "content_base64": base64.b64encode(stream.getvalue()).decode("ascii"),
            "line_items": len(items),
            "python_mismatches": mismatches,
            "calculated_subtotal_idr": float(python_check.get("calculated_line_subtotal") or Decimal(0)),
        }


__all__ = ["BoQExportService"]
