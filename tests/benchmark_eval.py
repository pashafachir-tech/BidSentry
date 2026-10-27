"""Benchmark deterministic checks on labelled fixtures and a public LPSE page.

The public-page result covers only the locally supported administrative checks
named in its label file. It is a small, manually mapped sample, not a field
accuracy estimate or a finding about bidder compliance.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bidsentry.config import Settings
from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest


SYNTHETIC_ROOT = ROOT / "data" / "sample_tenders"
PUBLIC_LPSE_ROOT = ROOT / "data" / "public_lpse"
LATENCY_REPETITIONS = 25


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _page_count(texts: list[str]) -> int:
    return sum(max(1, text.count("\f") + 1) for text in texts)


def _metrics_from_counts(true_positive: int, false_positive: int, false_negative: int) -> dict[str, Any]:
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def _metrics(predicted: set[str], expected: set[str]) -> dict[str, Any]:
    return _metrics_from_counts(
        len(predicted & expected),
        len(predicted - expected),
        len(expected - predicted),
    )


def _measure_evaluation(engine: EvaluationEngine, request_factory: Callable[[], EvaluationRequest]) -> tuple[dict[str, Any], float]:
    """Return the final deterministic output and mean latency after one warm-up."""
    engine.evaluate(request_factory())
    durations: list[float] = []
    result: dict[str, Any] = {}
    for _ in range(LATENCY_REPETITIONS):
        started = time.perf_counter()
        result = engine.evaluate(request_factory())
        durations.append((time.perf_counter() - started) * 1000)
    return result, sum(durations) / len(durations)


def _run_synthetic_regression(engine: EvaluationEngine) -> dict[str, Any]:
    totals = {"tp": 0, "fp": 0, "fn": 0}
    reports: list[dict[str, Any]] = []
    fixtures = sorted(SYNTHETIC_ROOT.glob("fixture_*/ground_truth.json"))
    if not fixtures:
        raise FileNotFoundError(f"No synthetic ground-truth fixtures found under {SYNTHETIC_ROOT}")
    for truth_path in fixtures:
        folder = truth_path.parent
        truth = json.loads(_read(truth_path))
        if truth.get("synthetic") is not True or not isinstance(truth.get("expected_issue_ids"), list):
            raise ValueError(f"Invalid synthetic ground truth: {truth_path}")
        tender_text = _read(folder / "dok_pemilihan.txt")
        evidence_text = _read(folder / "bukti_penyedia.txt")
        pages = _page_count([tender_text, evidence_text])
        result, duration_ms = _measure_evaluation(engine, lambda: EvaluationRequest(
            package_name=truth["fixture_id"],
            contract_value_idr=1_000_000_000,
            dok_pemilihan=tender_text,
            pustaka=evidence_text,
        ))
        predicted = {
            item["id"] for item in result["findings"]
            if item.get("status") in {"GAP", "EXPIRING", "SUPERSEDED"}
        }
        expected = set(truth["expected_issue_ids"])
        metrics = _metrics(predicted, expected)
        totals["tp"] += metrics["true_positive"]
        totals["fp"] += metrics["false_positive"]
        totals["fn"] += metrics["false_negative"]
        reports.append({
            "fixture_id": truth["fixture_id"],
            "pages": pages,
            "predicted_issue_ids": sorted(predicted),
            "expected_issue_ids": sorted(expected),
            **metrics,
            "latency_ms": round(duration_ms, 3),
            "latency_ms_per_page": round(duration_ms / pages, 3),
        })
    aggregate = _metrics_from_counts(totals["tp"], totals["fp"], totals["fn"])
    return {
        "dataset": "synthetic local regression fixtures",
        "fixture_count": len(reports),
        "metrics_scope": "issue-ID detection for GAP/EXPIRING/SUPERSEDED findings only",
        **aggregate,
        "latency_ms_per_page": round(
            sum(row["latency_ms"] for row in reports) / sum(row["pages"] for row in reports), 3
        ),
        "cases": reports,
    }


def _run_public_lpse(engine: EvaluationEngine) -> dict[str, Any]:
    totals = {"tp": 0, "fp": 0, "fn": 0}
    reports: list[dict[str, Any]] = []
    fixtures = sorted(PUBLIC_LPSE_ROOT.glob("*/ground_truth.json"))
    if not fixtures:
        raise FileNotFoundError(f"No public LPSE benchmark labels found under {PUBLIC_LPSE_ROOT}")
    for truth_path in fixtures:
        folder = truth_path.parent
        truth = json.loads(_read(truth_path))
        if truth.get("source_type") != "public_lpse_package_listing" or not truth.get("source_url"):
            raise ValueError(f"Public LPSE fixture must identify an official source URL: {truth_path}")
        expected_ids = truth.get("expected_check_ids")
        pages = truth.get("source_page_count")
        if not isinstance(expected_ids, list) or not expected_ids or not isinstance(pages, int) or pages < 1:
            raise ValueError(f"Public LPSE fixture has invalid labels or page count: {truth_path}")
        tender_text = _read(folder / "procurement_requirements.txt")
        result, duration_ms = _measure_evaluation(engine, lambda: EvaluationRequest(
            package_name=truth["fixture_id"],
            dok_pemilihan=tender_text,
            allow_external_processing=False,
        ))
        predicted = {
            item["id"] for item in result["findings"]
            if item.get("requirement_evidence")
        }
        expected = set(expected_ids)
        metrics = _metrics(predicted, expected)
        totals["tp"] += metrics["true_positive"]
        totals["fp"] += metrics["false_positive"]
        totals["fn"] += metrics["false_negative"]
        reports.append({
            "fixture_id": truth["fixture_id"],
            "source_url": truth["source_url"],
            "source_accessed": truth["source_accessed"],
            "pages": pages,
            "predicted_check_ids": sorted(predicted),
            "expected_check_ids": sorted(expected),
            "annotation_scope": truth["annotation_scope"],
            **metrics,
            "latency_ms": round(duration_ms, 3),
            "latency_ms_per_page": round(duration_ms / pages, 3),
        })
    aggregate = _metrics_from_counts(totals["tp"], totals["fp"], totals["fn"])
    return {
        "dataset": "public LPSE package listing",
        "fixture_count": len(reports),
        "label_count": sum(len(row["expected_check_ids"]) for row in reports),
        "metrics_scope": "precision/recall of supported requirement-check IDs found in the public tender page text",
        "annotation_note": "Single-maintainer labels; this small sample is not representative field validation.",
        **aggregate,
        "latency_ms_per_page": round(
            sum(row["latency_ms"] for row in reports) / sum(row["pages"] for row in reports), 3
        ),
        "cases": reports,
    }


def run_benchmark() -> dict[str, Any]:
    engine = EvaluationEngine(Settings.from_environment())
    return {
        "synthetic_regression": _run_synthetic_regression(engine),
        "real_lpse": _run_public_lpse(engine),
    }


def _print_metrics(label: str, report: dict[str, Any]) -> None:
    print(f"{label}: {report['dataset']}")
    print(f"Fixtures={report['fixture_count']} precision={report['precision']:.4f} recall={report['recall']:.4f} F1={report['f1']:.4f}")
    print(f"Mean latency/page={report['latency_ms_per_page']:.3f} ms ({LATENCY_REPETITIONS} runs after warm-up)")
    for row in report["cases"]:
        print(
            f"  {row['fixture_id']}: pages={row['pages']} TP={row['true_positive']} "
            f"FP={row['false_positive']} FN={row['false_negative']} "
            f"latency={row['latency_ms_per_page']:.3f} ms/page"
        )


def test_benchmark_empiris_lpse() -> None:
    """The requested pytest command reports metrics from a real public LPSE page."""
    report = run_benchmark()
    public_result = report["real_lpse"]
    _print_metrics("Benchmark riil terbatas", public_result)
    assert public_result["fixture_count"] >= 1
    assert public_result["label_count"] >= 1
    assert public_result["true_positive"] == public_result["label_count"]
    assert public_result["false_positive"] == 0
    assert public_result["false_negative"] == 0
    assert public_result["latency_ms_per_page"] >= 0


def test_synthetic_regression_metrics_remain_separate() -> None:
    report = run_benchmark()
    synthetic = report["synthetic_regression"]
    _print_metrics("Regression sintetis", synthetic)
    assert synthetic["fixture_count"] >= 1
    assert 0 <= synthetic["precision"] <= 1
    assert 0 <= synthetic["recall"] <= 1


def main() -> int:
    report = run_benchmark()
    _print_metrics("Benchmark riil terbatas", report["real_lpse"])
    _print_metrics("Regression sintetis (terpisah)", report["synthetic_regression"])
    print("Angka ini adalah metrik regression/eksploratif; bukan validasi lapangan yang representatif.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
