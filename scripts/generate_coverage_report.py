#!/usr/bin/env python3
"""
scripts/generate_coverage_report.py — ClaimFlow Coverage Report Generator
Executes pytest with coverage collection and compiles both an interactive HTML
report (htmlcov/index.html) and a human-readable Markdown report (coverage-report.md).
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
OUTPUT_MD = PROJECT_ROOT / "coverage-report.md"
HTML_COV_DIR = PROJECT_ROOT / "htmlcov"


def run_coverage() -> dict:
    """Run pytest with json and html coverage outputs."""
    print("Executing pytest with coverage instrumentation...")
    cov_json_path = BACKEND_DIR / "coverage.json"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=src",
        f"--cov-report=json:{cov_json_path}",
        f"--cov-report=html:{HTML_COV_DIR}",
        "-q",
    ]

    result = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True)
    if result.returncode not in {0, 1}:  # 0: all passed, 1: tests ran
        print(f"Warning: pytest exited with code {result.returncode}")
        print(result.stdout)
        print(result.stderr)

    if not cov_json_path.exists():
        raise RuntimeError(f"Coverage JSON not generated at {cov_json_path}")

    with open(cov_json_path, encoding="utf-8") as f:
        return json.load(f)


def make_progress_bar(pct: float, width: int = 15) -> str:
    """Render a text progress bar."""
    filled = int(round((pct / 100.0) * width))
    empty = width - filled
    return f"[{'#' * filled}{'.' * empty}]"


def generate_markdown(cov_data: dict) -> str:
    """Format coverage data into a structured GitHub-flavored Markdown report."""
    totals = cov_data.get("totals", {})
    files = cov_data.get("files", {})

    total_statements = totals.get("num_statements", 0)
    covered_statements = totals.get("covered_lines", 0)
    missing_statements = totals.get("missing_lines", 0)
    total_pct = totals.get("percent_covered", 0.0)

    # Calculate domain coverage
    domain_stmts = 0
    domain_covered = 0
    for filename, stats in files.items():
        if "src/claimflow/domain" in filename.replace("\\", "/"):
            summary = stats.get("summary", {})
            domain_stmts += summary.get("num_statements", 0)
            domain_covered += summary.get("covered_lines", 0)

    domain_pct = (domain_covered / domain_stmts * 100.0) if domain_stmts > 0 else 100.0
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    gate_status = "PASS" if total_pct >= 85.0 and domain_pct >= 85.0 else "FAIL"

    lines = [
        "# ClaimFlow Test Coverage & Quality Gate Report",
        "",
        f"> **Generated:** {now_str} | **Quality Gate 3:** `{gate_status}`",
        "",
        "## 1. Executive Summary & Quality Gates",
        "",
        "| Metric | Target | Actual | Evaluation Status |",
        "|---|:---:|:---:|:---:|",
        f"| **Overall Coverage** | $\\ge 85\\%$ | **{total_pct:.1f}%** | {'**PASS**' if total_pct >= 85 else '**FAIL**'} |",
        f"| **Domain Layer (`domain/`)** | $\\ge 85\\%$ | **{domain_pct:.1f}%** | {'**PASS**' if domain_pct >= 85 else '**FAIL**'} |",
        f"| **Total Statements** | - | **{total_statements}** | - |",
        f"| **Covered Statements** | - | **{covered_statements}** | - |",
        f"| **Missing Lines** | - | **{missing_statements}** | - |",
        "",
        "---",
        "",
        "## 2. Coverage by Subsystem & Module",
        "",
        "| Module / Component | Stmts | Miss | Cover % | Visual Progress |",
        "|---|:---:|:---:|:---:|:---:|",
    ]

    # Sort files alphabetically
    sorted_files = sorted(files.keys())
    for f in sorted_files:
        stats = files[f]["summary"]
        stmts = stats.get("num_statements", 0)
        if stmts == 0:
            continue
        miss = stats.get("missing_lines", 0)
        pct = stats.get("percent_covered", 0.0)
        bar = make_progress_bar(pct, width=12)

        # Normalize relative path
        rel_path = f.replace("\\", "/")
        if "src/claimflow/" in rel_path:
            rel_path = rel_path.split("src/claimflow/")[-1]

        lines.append(f"| `claimflow/{rel_path}` | {stmts} | {miss} | **{pct:.1f}%** | `{bar}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Coverage Report Artifacts",
        "- **Interactive HTML Report:** [`htmlcov/index.html`](file:///./htmlcov/index.html)",
        "- **Machine-readable XML:** [`coverage.xml`](file:///./backend/coverage.xml)",
        "- **Machine-readable JSON:** [`backend/coverage.json`](file:///./backend/coverage.json)",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    cov_data = run_coverage()
    md_content = generate_markdown(cov_data)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[OK] Readable coverage report written to: {OUTPUT_MD}")
    print(f"[OK] Interactive HTML coverage report written to: {HTML_COV_DIR / 'index.html'}")

    totals = cov_data.get("totals", {})
    print(
        f"\nTotal Coverage: {totals.get('percent_covered', 0.0):.1f}% "
        f"({totals.get('covered_lines', 0)}/{totals.get('num_statements', 0)} lines)"
    )


if __name__ == "__main__":
    main()
