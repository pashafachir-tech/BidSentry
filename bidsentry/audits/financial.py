"""Deterministic BoQ arithmetic, HPS deviation and Benford screening."""

from __future__ import annotations

import math
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from bidsentry.schemas.comprehensive import BoQLineItem


_ROW_PATTERNS = (
    re.compile(
        r"^\s*(?P<description>[^|]+)\|\s*(?:Volume\s*:\s*)?(?P<volume>[0-9.,]+)\s+(?P<unit>[^|]+)\|\s*(?:Harga\s*Satuan\s*:\s*)?(?:Rp\s*)?(?P<unit_price>[0-9][0-9.,]*)\s*\|\s*(?:Total\s*:\s*)?(?:Rp\s*)?(?P<total>[0-9][0-9.,]*)(?:\s*\|\s*(?:HPS\s*Satuan\s*:\s*)?(?:Rp\s*)?(?P<hps_unit_price>[0-9][0-9.,]*))?\s*$",
        re.IGNORECASE,
    ),
)
BENFORD_CHI_SQUARE_001 = 20.09  # Chi-square(8 df), alpha ~= 0.01; triage only.
HARGA_TIMPANG_HIGH = Decimal("1.10")
HARGA_TIMPANG_LOW = Decimal("0.80")


def parse_idr_number(value: Any) -> Decimal:
    """Parse common Indonesian currency strings as exact Decimal values."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    text = str(value).strip().replace("Rp", "").replace("rp", "").replace(" ", "")
    if not text:
        raise ValueError("Amount cannot be empty.")
    if "," in text and "." in text:
        # Indonesian display convention: dots group thousands, comma is decimal.
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        tail = text.rsplit(",", 1)[1]
        text = text.replace(",", ".") if len(tail) <= 2 else text.replace(",", "")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    elif "." in text and len(text.rsplit(".", 1)[1]) == 3:
        text = text.replace(".", "")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid currency amount: {value!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("Amount must be finite and non-negative.")
    return amount


def parse_boq_text(text: str) -> list[BoQLineItem]:
    """Parse delimited rows; structured `boq_items` remains the preferred input."""
    items: list[BoQLineItem] = []
    for line in text.splitlines():
        match = next((matched for pattern in _ROW_PATTERNS if (matched := pattern.match(line))), None)
        if not match:
            continue
        groups = match.groupdict()
        try:
            items.append(BoQLineItem(
                description=groups["description"].strip(),
                volume=parse_idr_number(groups["volume"]),
                unit=groups["unit"].strip(),
                unit_price_offered=parse_idr_number(groups["unit_price"]),
                total_offered=parse_idr_number(groups["total"]),
                hps_unit_price=parse_idr_number(groups["hps_unit_price"]) if groups.get("hps_unit_price") else None,
                source_quote=line.strip()[:4000],
            ))
        except (ValueError, InvalidOperation):
            continue
    return items


def parse_boq_tables(page_tables: list[dict[str, Any]]) -> list[BoQLineItem]:
    """Parse extracted PDF tables when their header columns are identifiable."""
    items: list[BoQLineItem] = []
    for table in page_tables:
        if not isinstance(table, dict) or not isinstance(table.get("rows"), list):
            continue
        page_ref = str(table.get("page_ref") or "") or None
        rows = table["rows"]
        header_index = next((
            index for index, row in enumerate(rows[:6])
            if isinstance(row, list) and _column_index(row, ("volume", "qty", "kuantitas")) is not None
            and _column_index(row, ("harga satuan", "unit price")) is not None
            and _column_index(row, ("total", "jumlah harga", "jumlah biaya")) is not None
        ), None)
        if header_index is None:
            continue
        header = rows[header_index]
        description_index = _column_index(header, ("uraian", "deskripsi", "description", "pekerjaan", "item"))
        volume_index = _column_index(header, ("volume", "qty", "kuantitas"))
        unit_index = _column_index(header, ("satuan", "unit"))
        price_index = _column_index(header, ("harga satuan", "unit price"), exclude=("hps", "oe", "owner"))
        total_index = _column_index(header, ("total", "jumlah harga", "jumlah biaya"))
        hps_index = _column_index(header, ("hps satuan", "harga satuan hps", "oe unit"))
        code_index = _column_index(header, ("kode", "code", "nomor", "no."))
        if None in (description_index, volume_index, unit_index, price_index, total_index):
            continue
        for row in rows[header_index + 1:]:
            if not isinstance(row, list) or len(row) <= max(description_index, volume_index, unit_index, price_index, total_index):
                continue
            description = str(row[description_index] or "").strip()
            unit = str(row[unit_index] or "").strip()
            if not description or not unit:
                continue
            try:
                items.append(BoQLineItem(
                    item_code=str(row[code_index]).strip()[:120] if code_index is not None and code_index < len(row) and row[code_index] else None,
                    description=description[:1000],
                    volume=parse_idr_number(row[volume_index]),
                    unit=unit[:80],
                    unit_price_offered=parse_idr_number(row[price_index]),
                    total_offered=parse_idr_number(row[total_index]),
                    hps_unit_price=parse_idr_number(row[hps_index]) if hps_index is not None and hps_index < len(row) and row[hps_index] else None,
                    page_ref=page_ref,
                ))
            except (ValueError, InvalidOperation):
                continue
    return items


def _column_index(headers: list[Any], terms: tuple[str, ...], exclude: tuple[str, ...] = ()) -> int | None:
    normalized = [re.sub(r"\s+", " ", str(value or "").casefold().replace("\n", " ")).strip() for value in headers]
    return next((index for index, header in enumerate(normalized) if any(term in header for term in terms) and not any(term in header for term in exclude)), None)


def audit_boq(
    items: list[BoQLineItem],
    offered_total_price: Decimal | None = None,
    hps_total_price: Decimal | None = None,
    source_pages: dict[str, str] | None = None,
) -> dict[str, Any]:
    discrepancies: list[dict[str, Any]] = []
    pricing_anomalies: list[dict[str, Any]] = []
    line_item_checks: list[dict[str, Any]] = []
    source_pages = source_pages or {}
    for index, item in enumerate(items, 1):
        calculated = item.volume * item.unit_price_offered
        difference = abs(calculated - item.total_offered)
        quote, citation_page, citation_status = _ground_quote(item, source_pages)
        math_status = "MATH_MISMATCH" if difference > Decimal("1.00") else "MATCH_WITHIN_TOLERANCE"
        line_item_checks.append({
            "item_code": item.item_code or f"BOQ-{index:04d}",
            "description": item.description,
            "page_ref": citation_page,
            "source_quote": quote,
            "citation_status": citation_status,
            "volume": _number(item.volume),
            "unit": item.unit,
            "unit_price_offered": _number(item.unit_price_offered),
            "stated_total": _number(item.total_offered),
            "calculated_total": _number(calculated),
            "absolute_difference": _number(difference),
            "math_status": math_status,
            "hps_unit_price": _number(item.hps_unit_price),
        })
        if difference > Decimal("1.00"):
            discrepancies.append({
                "item_code": item.item_code or f"BOQ-{index:04d}",
                "description": item.description,
                "page_ref": citation_page,
                "source_quote": quote,
                "citation_status": citation_status,
                "volume": _number(item.volume),
                "unit_price_offered": _number(item.unit_price_offered),
                "stated_total": _number(item.total_offered),
                "calculated_total": _number(calculated),
                "absolute_difference": _number(difference),
                "anomaly_type": "MATH_MISMATCH",
                "status": "MATH_MISMATCH",
            })
        if item.hps_unit_price is not None and item.hps_unit_price > 0:
            ratio = item.unit_price_offered / item.hps_unit_price
            anomaly_type = None
            if ratio > HARGA_TIMPANG_HIGH:
                anomaly_type = "HARGA_TIMPANG_HIGH"
            elif ratio < HARGA_TIMPANG_LOW and not (item.cost_analysis or "").strip():
                anomaly_type = "HARGA_TIMPANG_LOW"
            if anomaly_type:
                pricing_anomalies.append({
                    "item_code": item.item_code or f"BOQ-{index:04d}",
                    "description": item.description,
                    "page_ref": citation_page,
                    "source_quote": quote,
                    "citation_status": citation_status,
                    "unit_price_offered": _number(item.unit_price_offered),
                    "hps_unit_price": _number(item.hps_unit_price),
                    "variance_percentage": round(float((ratio - 1) * 100), 4),
                    "cost_analysis_provided": bool((item.cost_analysis or "").strip()),
                    "anomaly_type": anomaly_type,
                    "status": "REVIEW_REQUIRED",
                })

    calculated_subtotal = sum((item.volume * item.unit_price_offered for item in items), Decimal(0))
    stated_line_total_sum = sum((item.total_offered for item in items), Decimal(0))
    subtotal_check = None
    if items and offered_total_price is not None:
        delta = abs(calculated_subtotal - offered_total_price)
        subtotal_check = {
            "stated_total": _number(offered_total_price),
            "sum_of_line_totals": _number(calculated_subtotal),
            "sum_of_recalculated_line_totals": _number(calculated_subtotal),
            "sum_of_stated_line_totals": _number(stated_line_total_sum),
            "absolute_difference": _number(delta),
            "status": "MATH_MISMATCH" if delta > Decimal("1.00") else "MATCH_WITHIN_TOLERANCE",
        }
        if delta > Decimal("1.00"):
            discrepancies.append({"item_code": "BOQ-SUBTOTAL", "description": "Jumlah total semua baris dibanding total penawaran", "anomaly_type": "MATH_MISMATCH", **subtotal_check})

    offer_to_hps_ratio = None
    if offered_total_price is not None and hps_total_price is not None and hps_total_price > 0:
        offer_to_hps_ratio = round(float(offered_total_price / hps_total_price * 100), 4)

    benford = _benford_screen([item.unit_price_offered for item in items])
    return {
        "status": "screened" if items else "no_structured_boq_data",
        "line_item_count": len(items),
        "offered_total_price": _number(offered_total_price),
        "hps_total_price": _number(hps_total_price),
        "price_to_hps_ratio_percentage": offer_to_hps_ratio,
        "calculated_line_subtotal": _number(calculated_subtotal),
        "subtotal_check": subtotal_check,
        "line_item_checks": line_item_checks,
        "arithmetic_errors_detected": bool(discrepancies),
        "unbalanced_pricing_detected": bool(pricing_anomalies),
        "line_item_anomalies": discrepancies + pricing_anomalies,
        "benford_first_digit_screen": benford,
        "threshold_note": "Ambang 110%/80% adalah parameter skrining yang diminta pengguna, bukan ambang hukum universal.",
        "interpretation": "Anomali memerlukan verifikasi terhadap dokumen penawaran dan HPS asli; bukan bukti manipulasi atau dasar diskualifikasi otomatis.",
    }


def _ground_quote(item: BoQLineItem, source_pages: dict[str, str]) -> tuple[str | None, str | None, str]:
    quote = item.source_quote
    if not quote:
        return None, item.page_ref, "not_provided"
    if item.page_ref and item.page_ref in source_pages and quote in source_pages[item.page_ref]:
        return quote, item.page_ref, "verified_exact_substring"
    if item.page_ref is None:
        match = next((page_ref for page_ref, text in source_pages.items() if quote in text), None)
        if match:
            return quote, match, "verified_exact_substring"
    return None, item.page_ref, "unverified_quote_omitted"


def _benford_screen(values: list[Decimal]) -> dict[str, Any]:
    positive = [value for value in values if value > 0]
    if len(positive) < 40:
        return {"status": "not_run_insufficient_items", "sample_size": len(positive), "flag": False}
    counts = Counter()
    for value in positive:
        first = next((digit for digit in str(value.normalize()).lstrip("0.") if digit.isdigit() and digit != "0"), None)
        if first:
            counts[int(first)] += 1
    sample_size = sum(counts.values())
    if sample_size < 40:
        return {"status": "not_run_insufficient_valid_prices", "sample_size": sample_size, "flag": False}
    chi_square = 0.0
    observed = {}
    expected = {}
    for digit in range(1, 10):
        probability = math.log10(1 + 1 / digit)
        expected_count = sample_size * probability
        count = counts[digit]
        chi_square += (count - expected_count) ** 2 / expected_count
        observed[str(digit)] = count
        expected[str(digit)] = round(expected_count, 3)
    p_value = None
    try:
        from scipy.stats import chisquare
        p_value = float(chisquare(
            [counts[digit] for digit in range(1, 10)],
            [sample_size * math.log10(1 + 1 / digit) for digit in range(1, 10)],
        ).pvalue)
    except ImportError:
        # The fixed 8-df threshold remains available when SciPy is not installed.
        p_value = None
    return {
        "status": "screening_flag" if chi_square > BENFORD_CHI_SQUARE_001 else "no_screening_flag",
        "sample_size": sample_size,
        "observed_first_digits": observed,
        "expected_first_digits": expected,
        "chi_square": round(chi_square, 4),
        "p_value": round(p_value, 8) if p_value is not None else None,
        "threshold": BENFORD_CHI_SQUARE_001,
        "flag": chi_square > BENFORD_CHI_SQUARE_001,
        "interpretation": "Benford bukan uji kecurangan; tipe data dan proses pembentukan harga dapat melanggar distribusi Benford secara wajar.",
    }


def _number(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if value == value.to_integral_value() else float(value)


def run_financial_audit(
    items: list[BoQLineItem],
    offered_total_price: Decimal | None = None,
    hps_total_price: Decimal | None = None,
    source_pages: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return arithmetic proof rows and separately classified price signals."""
    from bidsentry.audits.pricing_imbalance import audit_pricing_imbalance
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
    """Recalculate structured BoQ rows and compare unit prices with HPS values."""
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

