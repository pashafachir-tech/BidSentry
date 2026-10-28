"""Held-out benchmark evaluation harness for BidSentry."""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bidsentry.evaluators.engine import EvaluationEngine, EvaluationRequest

BENCHMARK_DIR = Path("data/benchmark")
RESULTS_PATH = Path("docs/BENCHMARK_RESULTS.md")


def get_current_git_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"


def run_heldout_benchmark(save_to_markdown: bool = True, section_title: str = "Baseline Sebelum Perbaikan") -> dict[str, Any]:
    engine = EvaluationEngine()
    label_files = sorted(BENCHMARK_DIR.glob("*.labels.json"))
    assert len(label_files) >= 24, f"Held-out benchmark must contain at least 24 documents, found {len(label_files)}"

    # Stats per rule ID: { "TP": int, "FP": int, "FN": int, "docs_count": int }
    rule_stats = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "docs_count": 0})
    verdict_matches = 0
    trap_docs_total = 0
    trap_docs_clean = 0
    doc_results = []

    all_rule_ids = set()

    for path in label_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        doc_id = data["id"]
        inp = data["input"]
        expected_findings = {f["id"]: f["status"] for f in data.get("expected_findings", [])}
        forbidden_findings = set(data.get("forbidden_findings", []))
        expected_verdict = data.get("expected_verdict")
        is_trap = data.get("is_trap", False)

        all_rule_ids.update(expected_findings.keys())
        all_rule_ids.update(forbidden_findings)

        req = EvaluationRequest(**inp)
        res = engine.evaluate(req)

        actual_findings = {f["id"]: f["status"] for f in res.get("findings", [])}
        all_rule_ids.update(actual_findings.keys())

        # Evaluate verdict
        actual_verdict = res.get("verdict")
        if actual_verdict == expected_verdict:
            verdict_matches += 1

        # Evaluate trap evasion
        had_forbidden = any(fid in actual_findings for fid in forbidden_findings)
        if is_trap:
            trap_docs_total += 1
            if not had_forbidden:
                trap_docs_clean += 1

        # Check TP, FP, FN for this document
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
            "id": doc_id,
            "title": data.get("title", ""),
            "expected_verdict": expected_verdict,
            "actual_verdict": actual_verdict,
            "expected_count": len(expected_findings),
            "actual_count": len(actual_findings),
            "is_trap": is_trap,
            "trap_clean": not had_forbidden if is_trap else None,
        })

    # Calculate precision and recall per rule
    rule_table = []
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for fid in sorted(all_rule_ids):
        stats = rule_stats[fid]
        tp = stats["TP"]
        fp = stats["FP"]
        fn = stats["FN"]
        total_tp += tp
        total_fp += fp
        total_fn += fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
        rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
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
    verdict_acc = verdict_matches / len(label_files)
    trap_rate = trap_docs_clean / trap_docs_total if trap_docs_total else 1.0

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_current_git_commit(),
        "total_documents": len(label_files),
        "section_title": section_title,
        "verdict_accuracy": verdict_acc,
        "trap_evasion_rate": trap_rate,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": overall_f1,
        "rules": rule_table,
        "documents": doc_results,
    }

    if save_to_markdown:
        _write_markdown_report(summary, RESULTS_PATH, section_title)

    return summary


def _write_markdown_report(summary: dict[str, Any], path: Path, section_title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_content = path.read_text(encoding="utf-8") if path.is_file() else ""

    md_lines = [
        f"## {section_title}",
        "",
        f"- **Tanggal:** {summary['timestamp'][:10]} ({summary['timestamp']})",
        f"- **Commit Hash:** `{summary['git_commit']}`",
        f"- **Jumlah Dokumen Uji:** {summary['total_documents']} dokumen sintetis held-out (termasuk 8 kasus jebakan/negatif)",
        f"- **Verdict Accuracy:** {summary['verdict_accuracy'] * 100:.1f}% ({round(summary['verdict_accuracy'] * summary['total_documents'])}/{summary['total_documents']})",
        f"- **Trap Evasion Rate:** {summary['trap_evasion_rate'] * 100:.1f}% (tingkat ketepatan menghindari false flag pada klausul jebakan)",
        f"- **Macro Precision:** {summary['macro_precision'] * 100:.1f}%",
        f"- **Macro Recall:** {summary['macro_recall'] * 100:.1f}%",
        f"- **Macro F1 Score:** {summary['macro_f1'] * 100:.1f}%",
        "",
        "### Tabel Akurasi Per Aturan / Temuan",
        "",
        "| Aturan (Rule ID) | Dokumen Relevan | TP | FP | FN | Precision | Recall | F1 Score | Keterangan Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for r in summary["rules"]:
        prec_pct = f"{r['precision'] * 100:.1f}%"
        rec_pct = f"{r['recall'] * 100:.1f}%"
        f1_pct = f"{r['f1'] * 100:.1f}%"
        status_note = "Aman (Precision ≥ 80%)" if r["precision"] >= 0.8 else "**Perlu Perbaikan (Precision < 80%)**"
        md_lines.append(f"| `{r['rule_id']}` | {r['docs_count']} | {r['tp']} | {r['fp']} | {r['fn']} | {prec_pct} | {rec_pct} | {f1_pct} | {status_note} |")

    md_lines.append("")

    new_section = "\n".join(md_lines)
    if not existing_content:
        full_content = "# Hasil Benchmark Independen BidSentry (Held-out Dataset)\n\n" + new_section
    elif f"## {section_title}" in existing_content:
        # Replace existing section
        parts = existing_content.split(f"## {section_title}")
        prefix = parts[0]
        remainder = parts[1]
        next_section_idx = remainder.find("\n## ")
        suffix = remainder[next_section_idx:] if next_section_idx != -1 else ""
        full_content = prefix.rstrip() + "\n\n" + new_section + suffix.lstrip()
    else:
        full_content = existing_content.rstrip() + "\n\n" + new_section

    path.write_text(full_content + "\n", encoding="utf-8")


def test_heldout_benchmark_runs() -> None:
    results = run_heldout_benchmark(save_to_markdown=True, section_title="Baseline Sebelum Perbaikan (Initial Baseline)")
    assert results["total_documents"] == 24
    assert RESULTS_PATH.is_file()
