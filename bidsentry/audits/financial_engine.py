"""Combined deterministic BoQ, HPS imbalance, and Benford audit facade."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from bidsentry.audits.financial import audit_boq, parse_boq_tables, parse_boq_text, parse_idr_number
from bidsentry.audits.pricing_imbalance import audit_pricing_imbalance
from bidsentry.schemas.comprehensive import BoQLineItem


def run_financial_audit(
    items: list[BoQLineItem],
    offered_total_price: Decimal | None = None,
    hps_total_price: Decimal | None = None,
    source_pages: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return arithmetic proof rows and separately classified price signals."""
    arithmetic = audit_boq(items, offered_total_price, hps_total_price, source_pages)
    imbalance = audit_pricing_imbalance(items, source_pages=source_pages)
    arithmetic["pricing_imbalance"] = imbalance
    arithmetic["benford_first_digit_screen"] = {
        **arithmetic.get("benford_first_digit_screen", {}),
        "minimum_item_count": 40,
        "method": "Pearson chi-square goodness-of-fit against Benford first-digit probabilities; triage only.",
    }
    return arithmetic


def audit_boq_table(table_data: list[dict[str, Any]], hps_data: dict[str, Any]) -> dict[str, Any]:
    """Recalculate structured BoQ rows and compare unit prices with HPS values.

    HPS values may be embedded in each row, supplied in ``hps_data['items']``
    as rows, or keyed by item code/description in the top-level mapping.
    """

    hps_lookup = _build_hps_lookup(hps_data)
    items: list[BoQLineItem] = []
    invalid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(table_data, 1):
        if not isinstance(row, dict):
            invalid_rows.append({"row": index, "error": "row_must_be_an_object"})
            continue
        code = _row_value(row, "item_code", "code", "item", "id")
        description = _row_value(row, "description", "uraian", "item_name", "name")
        volume = _row_value(row, "volume", "qty", "quantity", "kuantitas")
        unit = _row_value(row, "unit", "satuan")
        unit_price = _row_value(row, "unit_price_offered", "unit_price", "price", "harga_satuan")
        stated_total = _row_value(row, "stated_total", "total_offered", "total", "amount", "jumlah")
        row_hps = _row_value(row, "hps_unit_price", "hps_price", "reference_unit_price")
        if row_hps is None:
            row_hps = hps_lookup.get(str(code).strip().casefold()) if code is not None else None
        if row_hps is None and description is not None:
            row_hps = hps_lookup.get(str(description).strip().casefold())
        try:
            if description is None or volume is None or unit is None or unit_price is None or stated_total is None:
                raise ValueError("required_columns_missing")
            item = BoQLineItem(
                item_code=str(code)[:120] if code is not None else None,
                description=str(description).strip()[:1000],
                volume=parse_idr_number(volume),
                unit=str(unit).strip()[:80],
                unit_price_offered=parse_idr_number(unit_price),
                total_offered=parse_idr_number(stated_total),
                hps_unit_price=parse_idr_number(row_hps) if row_hps is not None else None,
                cost_analysis=None,
            )
        except (ValueError, TypeError, InvalidOperation) as exc:
            invalid_rows.append({"row": index, "item_code": str(code)[:120] if code is not None else None, "error": str(exc)[:240]})
            continue
        items.append(item)

    offered_total = _optional_amount(_row_value(hps_data, "offered_total_price", "bid_total", "offer_total"))
    hps_total = _optional_amount(_row_value(hps_data, "hps_total_price", "total_hps", "hps_total"))
    result = audit_boq(items, offered_total, hps_total)
    result["invalid_rows"] = invalid_rows
    result["input_row_count"] = len(table_data)
    result["validated_row_count"] = len(items)
    result["benford_first_digit_screen"] = {
        **result.get("benford_first_digit_screen", {}),
        "minimum_item_count": 40,
        "method": "Pearson chi-square goodness-of-fit against Benford first-digit probabilities; triage only.",
    }
    return result


def _build_hps_lookup(hps_data: dict[str, Any]) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    hps_rows = hps_data.get("items")
    if isinstance(hps_rows, list):
        for row in hps_rows:
            if not isinstance(row, dict):
                continue
            key = _row_value(row, "item_code", "code", "item", "description", "uraian", "name")
            value = _row_value(row, "hps_unit_price", "unit_price", "unit_price_hps", "price", "harga_satuan")
            if key is not None and value is not None:
                lookup[str(key).strip().casefold()] = value
    elif isinstance(hps_rows, dict):
        for key, value in hps_rows.items():
            if isinstance(value, dict):
                value = _row_value(value, "hps_unit_price", "unit_price", "unit_price_hps", "price", "harga_satuan")
            if value is not None:
                lookup[str(key).strip().casefold()] = value
    for key, value in hps_data.items():
        if key in {"items", "offered_total_price", "bid_total", "offer_total", "hps_total_price", "total_hps", "hps_total"}:
            continue
        if isinstance(value, dict):
            value = _row_value(value, "hps_unit_price", "unit_price", "unit_price_hps", "price", "harga_satuan")
        if value is not None:
            lookup[str(key).strip().casefold()] = value
    return lookup


def _row_value(row: dict[str, Any], *keys: str) -> Any:
    normalized = {str(key).casefold(): value for key, value in row.items()}
    return next((normalized[key.casefold()] for key in keys if key.casefold() in normalized), None)


def _optional_amount(value: Any) -> Decimal | None:
    return parse_idr_number(value) if value is not None else None


__all__ = ["audit_boq", "audit_boq_table", "parse_boq_tables", "parse_boq_text", "run_financial_audit"]
