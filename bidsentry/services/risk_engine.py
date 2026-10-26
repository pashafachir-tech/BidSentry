"""Deterministic triage scoring. This is a review index, not fraud probability."""

from __future__ import annotations

from typing import Any


STATUS_POINTS = {"GAP": 25, "EXPIRING": 15, "SUPERSEDED": 8, "REVIEW": 0, "TERPENUHI": 0}


def level_for_score(score: int) -> str:
    if score >= 70:
        return "CRITICAL"
    if score >= 40:
        return "HIGH"
    if score >= 20:
        return "MEDIUM"
    return "LOW"


def score_findings(findings: list[dict[str, Any]], anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    drivers: list[dict[str, Any]] = []
    total = 0
    for finding in findings:
        points = STATUS_POINTS.get(str(finding.get("status", "")), 0)
        if points:
            total += points
            drivers.append({"label": finding.get("clause", finding.get("id", "Klausul")), "points": points, "source": finding.get("source", "Dokumen")})
    for anomaly in anomalies:
        points = int(anomaly.get("points", 18))
        total += points
        drivers.append({"label": anomaly.get("title", "Anomali kontrak"), "points": points, "source": anomaly.get("source", "Dokumen kontrak")})
    score = min(100, total)
    level = level_for_score(score)
    drivers.sort(key=lambda item: item["points"], reverse=True)
    return {
        "score": score,
        "level": level,
        "method": "rules-based-triage-v1",
        "calibrated": False,
        "drivers": drivers[:6],
    }
