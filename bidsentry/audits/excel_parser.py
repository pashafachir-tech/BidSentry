"""Deterministic Excel (.xlsx) parser for Bill of Quantities (BoQ) and HPS data."""

from __future__ import annotations

import io
from typing import Any

import openpyxl


def parse_boq_excel(file_bytes: bytes) -> dict[str, Any]:
    """Parse an Excel file containing a Bill of Quantities (BoQ) or HPS table."""
    wb = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), data_only=True)
    sheet = wb.active
    if not sheet:
        return {"items": [], "total_idr": 0.0, "text": "File Excel tidak memiliki sheet aktif."}

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return {"items": [], "total_idr": 0.0, "text": "Sheet Excel kosong."}

    # Find header row
    header_idx = -1
    col_mapping: dict[str, int] = {}
    for idx, row in enumerate(rows[:20]):
        row_str = [str(cell).strip().lower() for cell in row if cell is not None]
        has_desc = any("uraian" in c or "deskripsi" in c or "pekerjaan" in c or "item" in c for c in row_str)
        has_total = any("total" in c or "jumlah" in c or "harga" in c for c in row_str)
        if has_desc and has_total:
            header_idx = idx
            for c_idx, cell in enumerate(row):
                if cell is None:
                    continue
                cl = str(cell).strip().lower()
                if "no" in cl and "rekening" not in cl:
                    col_mapping.setdefault("no", c_idx)
                elif "uraian" in cl or "deskripsi" in cl or "pekerjaan" in cl or "item" in cl:
                    col_mapping.setdefault("desc", c_idx)
                elif "vol" in cl or "qty" in cl or "kuantitas" in cl:
                    col_mapping.setdefault("vol", c_idx)
                elif "satuan" in cl or "unit" in cl:
                    col_mapping.setdefault("unit", c_idx)
                elif "harga satuan" in cl or "unit price" in cl or "tarif" in cl:
                    col_mapping.setdefault("price", c_idx)
                elif "total" in cl or "jumlah" in cl or "subtotal" in cl:
                    col_mapping.setdefault("total", c_idx)
            break

    items: list[dict[str, Any]] = []
    text_lines: list[str] = ["=== HASIL PEMBACAAN BILL OF QUANTITIES (BoQ / HPS) ==="]

    start_row = header_idx + 1 if header_idx != -1 else 0
    calculated_total = 0.0

    for r_idx, row in enumerate(rows[start_row:], start=start_row + 1):
        if not any(row):
            continue
        desc_val = str(row[col_mapping.get("desc", 1)] or "").strip() if len(row) > col_mapping.get("desc", 1) else ""
        if not desc_val or desc_val.lower().startswith(("total", "jumlah", "grand total")):
            continue

        no_val = str(row[col_mapping.get("no", 0)] or r_idx) if len(row) > col_mapping.get("no", 0) else str(r_idx)
        vol_val = row[col_mapping.get("vol", 2)] if len(row) > col_mapping.get("vol", 2) else 1
        unit_val = str(row[col_mapping.get("unit", 3)] or "unit") if len(row) > col_mapping.get("unit", 3) else "unit"
        price_val = row[col_mapping.get("price", 4)] if len(row) > col_mapping.get("price", 4) else None
        tot_val = row[col_mapping.get("total", 5)] if len(row) > col_mapping.get("total", 5) else None

        try:
            tot_num = float(tot_val) if tot_val is not None else float(price_val or 0) * float(vol_val or 1)
        except (ValueError, TypeError):
            tot_num = 0.0

        calculated_total += tot_num
        item_entry = {
            "no": no_val,
            "description": desc_val,
            "volume": vol_val,
            "unit": unit_val,
            "unit_price": price_val,
            "total": tot_num,
        }
        items.append(item_entry)
        text_lines.append(f"{no_val}. {desc_val} | Vol: {vol_val} {unit_val} | Total: Rp {tot_num:,.0f}".replace(",", "."))

    text_lines.append(f"\nTOTAL BIAYA BoQ: Rp {calculated_total:,.0f}".replace(",", "."))
    return {
        "items": items,
        "total_idr": calculated_total,
        "text": "\n".join(text_lines),
    }
