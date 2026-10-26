"""Contract-delay penalty parser and transparent what-if arithmetic."""

from __future__ import annotations

import re
from typing import Any


_RATE = re.compile(r"(?P<n>\d+(?:[.,]\d+)?)\s*/\s*(?P<d>\d{3,})|(?P<per_mille>\d+(?:[.,]\d+)?)\s*(?:‰|permil|per\s*mille)|(?P<pct>\d+(?:[.,]\d+)?)\s*%", re.I)
_CAP = re.compile(r"(?:maksimum|maksimal|paling\s+tinggi|batas\s+(?:maksimum|paling\s+tinggi)|tidak\s+lebih\s+dari|dibatasi\s+sebesar)\D{0,40}(\d+(?:[.,]\d+)?)\s*%", re.I)


def _decimal(value: str) -> float:
    return float(value.replace(",", "."))


def _parse_rate(text: str) -> float | None:
    match = _RATE.search(text)
    if not match:
        return None
    if match.group("n"):
        denominator = float(match.group("d"))
        return _decimal(match.group("n")) / denominator if denominator else None
    if match.group("per_mille"):
        return _decimal(match.group("per_mille")) / 1000
    return _decimal(match.group("pct")) / 100


def calculate_penalty_scenarios(
    contract_value_idr: float,
    clause_text: str,
    *,
    delay_days: tuple[int, ...] = (10, 30, 50),
    statutory_daily_rate: float = 0.001,
    illustrative_cap_percentage: float = 0.05,
) -> dict[str, Any]:
    """Compute contract and comparison scenarios without making a legal finding.

    Perpres 16/2018 as amended through Perpres 46/2025 specifies a 1‰ daily
    delay fine in the cited provision. A 5% cap is exposed only as an
    illustrative assumption and must not be presented as the statutory cap.
    """
    if isinstance(contract_value_idr, bool) or contract_value_idr < 0:
        raise ValueError("contract_value_idr must be a non-negative number")
    if not 0 < statutory_daily_rate < 1 or not 0 < illustrative_cap_percentage <= 1:
        raise ValueError("Penalty rate and cap must be within valid percentage bounds")
    lines = [line.strip() for line in clause_text.splitlines() if line.strip()]
    penalty_lines = [line for line in lines if re.search(r"denda|sanksi\s+keterlambatan|liquidated\s+damages", line, re.I)]
    clause = " ".join(penalty_lines)[:1200]
    contract_rate = _parse_rate(clause) if clause else None
    cap_match = _CAP.search(clause) if clause else None
    clause_cap = _decimal(cap_match.group(1)) / 100 if cap_match else None
    uncapped = bool(penalty_lines and clause_cap is None)
    scenarios: list[dict[str, Any]] = []
    for days in delay_days:
        if isinstance(days, bool) or days < 0:
            raise ValueError("delay_days must contain non-negative integers")
        contractual_raw = contract_value_idr * (contract_rate or statutory_daily_rate) * days
        contractual_value = min(contractual_raw, contract_value_idr * clause_cap) if clause_cap is not None else contractual_raw
        statutory_comparison_raw = contract_value_idr * statutory_daily_rate * days
        illustrative_cap = contract_value_idr * illustrative_cap_percentage
        scenarios.append({
            "delay_days": days,
            "contract_clause_amount_idr": round(contractual_value, 2),
            "contract_clause_amount_uncapped_idr": round(contractual_raw, 2),
            "contract_clause_vs_illustrative_cap_excess_idr": round(max(0, contractual_value - illustrative_cap), 2),
            "1_per_mille_daily_comparison_idr": round(statutory_comparison_raw, 2),
            "illustrative_5_percent_cap_amount_idr": round(min(statutory_comparison_raw, illustrative_cap), 2),
            "illustrative_cap_excess_idr": round(max(0, contractual_value - illustrative_cap), 2),
            "statutory_comparison_cap_excess_idr": round(max(0, statutory_comparison_raw - illustrative_cap), 2),
        })
    alerts: list[str] = []
    if uncapped:
        alerts.append("CRITICAL_POISON_PILL")
    if contract_rate is not None and contract_rate > statutory_daily_rate:
        alerts.append("CONTRACT_RATE_ABOVE_1_PER_MILLE_COMPARISON")
    if not penalty_lines:
        alerts.append("PENALTY_CLAUSE_NOT_FOUND")
    return {
        "status": "calculated" if contract_value_idr > 0 else "contract_value_required",
        "contract_value_idr": round(contract_value_idr, 2),
        "clause_quote": clause or None,
        "contract_daily_rate": contract_rate,
        "contract_cap_percentage": clause_cap,
        "uncapped_clause_detected": uncapped,
        "alerts": alerts,
        "scenarios": scenarios,
        "assumptions": {
            "daily_comparison_rate": statutory_daily_rate,
            "daily_rate_source": "Perpres 16/2018 jo. Perpres 12/2021 jo. Perpres 46/2025, Pasal 78 ayat (5) huruf f (konsolidasi LKPP)",
            "illustrative_cap_percentage": illustrative_cap_percentage,
            "cap_note": "Batas 5% adalah asumsi simulasi, bukan batas maksimum yang dinyatakan sebagai standar umum pada ketentuan denda harian tersebut.",
        },
        "review_note": "Aritmetika ini bukan nasihat hukum. Cocokkan basis pengenaan (nilai kontrak atau bagian kontrak), klausul final, dan aturan yang berlaku pada tanggal paket.",
    }
