"""Independent benchmark evaluator for narrative prose budget parsing.

Evaluates free-prose budget and HPS extraction against Pagu DIPA on 5 dedicated documents.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest

BUDGET_DIR = Path(__file__).resolve().parent.parent / "data" / "test_narrative_budget"


def run_budget_narrative_benchmark() -> dict[str, Any]:
    engine = EvaluationEngine()
    test_files = sorted(BUDGET_DIR.glob("*.json"))

    if not test_files:
        raise FileNotFoundError(f"No narrative budget test files found in {BUDGET_DIR}")

    rule_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "docs_count": 0})
    verdict_matches = 0
    trap_docs_total = 0
    trap_docs_clean = 0
    doc_results: list[dict[str, Any]] = []
    all_rule_ids: set[str] = set()

    for path in test_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        req_data = data.get("request", {})
        expected_verdict = data.get("expected_verdict")
        expected_findings = data.get("expected_findings", {})
        forbidden_findings = set(data.get("forbidden_findings", []))
        is_trap = data.get("is_trap", False)

        request = EvaluationRequest(**req_data)
        eval_result = engine.evaluate(request)

        actual_verdict = eval_result.get("verdict", "")
        if actual_verdict == expected_verdict:
            verdict_matches += 1

        actual_findings_list = eval_result.get("findings", [])
        actual_findings = {f["id"]: f.get("status", f.get("severity", "")) for f in actual_findings_list}

        for fid in expected_findings:
            all_rule_ids.add(fid)
        for fid in actual_findings:
            all_rule_ids.add(fid)

        # Check traps
        had_forbidden = False
        if is_trap:
            trap_docs_total += 1
            for fid in forbidden_findings:
                if fid in actual_findings:
                    act_status = str(actual_findings[fid]).upper()
                    if act_status in ("GAP", "EXPIRING", "CRITICAL", "HIGH"):
                        had_forbidden = True
                        break
            if not had_forbidden:
                trap_docs_clean += 1

        # Check TP, FP, FN
        doc_matched_rules = set()
        for fid, exp_status in expected_findings.items():
            rule_stats[fid]["docs_count"] += 1
            doc_matched_rules.add(fid)
            if fid in actual_findings and actual_findings[fid] == exp_status:
                rule_stats[fid]["TP"] += 1
            else:
                rule_stats[fid]["FN"] += 1

        for fid, act_status in actual_findings.items():
            if fid not in expected_findings or expected_findings[fid] != act_status:
                rule_stats[fid]["FP"] += 1
                if fid not in doc_matched_rules:
                    rule_stats[fid]["docs_count"] += 1

        doc_results.append({
            "id": data.get("id", path.stem),
            "title": data.get("title", ""),
            "expected_verdict": expected_verdict,
            "actual_verdict": actual_verdict,
            "verdict_match": actual_verdict == expected_verdict,
            "expected_count": len(expected_findings),
            "actual_count": len(actual_findings),
            "is_trap": is_trap,
            "trap_clean": not had_forbidden if is_trap else None,
        })

    rule_table = []
    for fid in sorted(all_rule_ids):
        stats = rule_stats[fid]
        tp = stats["TP"]
        fp = stats["FP"]
        fn = stats["FN"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if stats["docs_count"] == 0 and fp == 0 else 0.0)
        rec = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if stats["docs_count"] == 0 and fn == 0 else 0.0)
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        rule_table.append({
            "rule_id": fid,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "docs_count": stats["docs_count"],
            "precision": prec,
            "recall": rec,
            "f1": f1,
        })

    macro_precision = sum(r["precision"] for r in rule_table) / len(rule_table) if rule_table else 0.0
    macro_recall = sum(r["recall"] for r in rule_table) / len(rule_table) if rule_table else 0.0
    overall_f1 = (2 * macro_precision * macro_recall) / (macro_precision + macro_recall) if (macro_precision + macro_recall) > 0 else 0.0
    verdict_acc = verdict_matches / len(test_files)
    trap_rate = trap_docs_clean / trap_docs_total if trap_docs_total else 1.0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_documents": len(test_files),
        "verdict_accuracy": verdict_acc,
        "trap_evasion_rate": trap_rate,
        "trap_docs_total": trap_docs_total,
        "trap_docs_clean": trap_docs_clean,
        "verdict_matches": verdict_matches,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": overall_f1,
        "rules": rule_table,
        "documents": doc_results,
    }


def test_budget_narrative_benchmark_runs() -> None:
    results = run_budget_narrative_benchmark()
    assert results["total_documents"] == 5
    print(f"\n[NARRATIVE BUDGET TEST RESULTS] Verdict Acc: {results['verdict_accuracy']*100:.1f}%, Trap Evasion: {results['trap_evasion_rate']*100:.1f}%, Macro F1: {results['macro_f1']*100:.1f}%")


if __name__ == "__main__":
    res = run_budget_narrative_benchmark()
    print("=" * 60)
    print("BID SENTRY - PROSE BUDGET BENCHMARK EVALUATION (5 DOCS)")
    print("=" * 60)
    print(f"Total Dokumen Uji     : {res['total_documents']}")
    print(f"Verdict Accuracy      : {res['verdict_accuracy']*100:.1f}% ({res['verdict_matches']}/{res['total_documents']})")
    print(f"Trap Evasion Rate     : {res['trap_evasion_rate']*100:.1f}% ({res['trap_docs_clean']}/{res['trap_docs_total']})")
    print(f"Macro Precision       : {res['macro_precision']*100:.1f}%")
    print(f"Macro Recall          : {res['macro_recall']*100:.1f}%")
    print(f"Macro F1 Score        : {res['macro_f1']*100:.1f}%")
    print("\nDetail Hasil per Dokumen:")
    for d in res["documents"]:
        status = "[MATCH]" if d["verdict_match"] else "[MISMATCH]"
        trap_str = f"(Trap: {'PASS' if d['trap_clean'] else 'FAIL'})" if d["is_trap"] else ""
        print(f"  {status} {d['id']}: Expected={d['expected_verdict']}, Actual={d['actual_verdict']} {trap_str}")
