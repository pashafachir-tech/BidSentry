"""Financial audit engine facade.

All core financial calculations are unified in `bidsentry.audits.financial`.
This module provides backward-compatible imports for `run_financial_audit`,
`audit_boq_table`, `audit_boq`, `parse_boq_tables`, and `parse_boq_text`.
"""

from __future__ import annotations

from bidsentry.audits.financial import (
    audit_boq,
    audit_boq_table,
    parse_boq_tables,
    parse_boq_text,
    parse_idr_number,
    run_financial_audit,
)

__all__ = [
    "audit_boq",
    "audit_boq_table",
    "parse_boq_tables",
    "parse_boq_text",
    "parse_idr_number",
    "run_financial_audit",
]
