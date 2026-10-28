"""Test to prevent hardcoded percentage strings in benchmark reporting templates.

Ensures that all benchmark metrics in reporting templates are computed dynamically.
"""

from pathlib import Path
import re

BENCHMARK_HELDOUT_PATH = Path(__file__).resolve().parent / "benchmark_heldout.py"


def test_no_hardcoded_percentages_in_heldout_template():
    code = BENCHMARK_HELDOUT_PATH.read_text(encoding="utf-8")
    
    # Locate _write_markdown_report function body
    assert "def _write_markdown_report" in code, "_write_markdown_report must exist"
    func_body = code.split("def _write_markdown_report")[1].split("def test_heldout_benchmark_runs")[0]
    
    # Look for table rows with hardcoded percentage literals like '100.0%' or '+25.0%' or '+17.9%' inside literal strings
    # Any line with | ... % ... | in a static string (not an f-string expression) should be flagged
    for line in func_body.splitlines():
        line = line.strip()
        if line.startswith('"|') or line.startswith("'|"):
            # This is a literal table row string!
            # Check if it contains hardcoded percentage values
            hardcoded_pct = re.findall(r"\b\d+\.\d+%", line)
            assert not hardcoded_pct, f"Found hardcoded static percentage in template row: {line}"
            # Check for hardcoded ratio strings like (8/8) or (24/24)
            hardcoded_ratio = re.findall(r"\(\d+/\d+\)", line)
            assert not hardcoded_ratio, f"Found hardcoded ratio in template row: {line}"
