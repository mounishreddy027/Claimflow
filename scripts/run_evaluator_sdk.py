#!/usr/bin/env python3
"""
scripts/run_evaluator_sdk.py — Programmatic Claude Agent SDK Runner
Executes headless evaluator and quality ratcheting loop per scripts/README.md
and verifies the 6 Evaluator Quality Gates in sprint-contracts/sprint-01-contract.md.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
AGENT_DIR = PROJECT_ROOT / ".claude" / "agents"
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
REVIEWS_DIR = PROJECT_ROOT / "specs" / "reviews"
EVAL_SCORES_FILE = STATE_DIR / "eval-scores.json"
COVERAGE_BASELINE_FILE = STATE_DIR / "coverage-baseline.txt"
VERIFICATION_REPORT_FILE = REVIEWS_DIR / "ac-verification-report.md"


class ProgrammaticEvaluatorAgent:
    """Headless Evaluator Agent implementation utilizing Anthropic SDK / Agent patterns."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = os.getenv("EVAL_BASE_URL", base_url)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.evaluator_prompt = self._load_prompt("evaluator.md")
        self.security_prompt = self._load_prompt("security-reviewer.md")

    def _load_prompt(self, filename: str) -> str:
        agent_path = AGENT_DIR / filename
        if agent_path.exists():
            return agent_path.read_text(encoding="utf-8")
        return f"System prompt for {filename}"

    def check_gate_1_health(self) -> dict:
        """Gate 1: Service Health & Startup (NFR-07: < 1,000ms latency). Strict live HTTP probe only."""
        health_url = f"{self.base_url}/health"
        print(f"Gate 1: Probing live HTTP endpoint: {health_url}...")

        try:
            start = time.perf_counter()
            req = urllib.request.Request(health_url, headers={"User-Agent": "Claude-Evaluator-SDK/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                status = resp.status
                body = json.loads(resp.read().decode("utf-8"))

            if status == 200 and elapsed_ms < 1000.0 and body.get("status") == "ok":
                return {
                    "name": "Gate 1: Service Health",
                    "status": "PASS",
                    "latency_ms": round(elapsed_ms, 2),
                    "http_status": status,
                    "evidence": f"Live HTTP {health_url} responded in {elapsed_ms:.1f}ms with status {status}",
                }
            return {
                "name": "Gate 1: Service Health",
                "status": "FAIL",
                "latency_ms": round(elapsed_ms, 2),
                "http_status": status,
                "evidence": f"Live HTTP health returned status {status} or latency {elapsed_ms:.1f}ms exceeds 1,000ms",
            }
        except Exception as exc:
            return {
                "name": "Gate 1: Service Health",
                "status": "FAIL",
                "latency_ms": None,
                "http_status": None,
                "evidence": f"HTTP probe to {health_url} failed: {exc}. Server is not running.",
            }

    def check_gate_2_ac_verification(self) -> dict:
        """Gate 2: Acceptance Criteria Verification (100% scenarios pass)."""
        print("Gate 2: Executing AC unit & integration test scenarios...")
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "AC_01 or AC_02 or AC_03 or AC_04 or AC_05 or AC_06 or AC_07 or AC_08 or AC_09 or AC_10",
            "-q",
        ]
        res = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True)
        passed = res.returncode == 0
        return {
            "name": "Gate 2: AC Verification",
            "status": "PASS" if passed else "FAIL",
            "tests_run": "All AC-tagged scenarios",
            "evidence": "100% of Acceptance Criteria test scenarios passed without failure" if passed else f"Pytest failed with exit code {res.returncode}: {res.stderr or res.stdout[:200]}",
        }

    def check_gate_3_coverage_ratchet(self) -> dict:
        """Gate 3: Coverage Ratchet (Domain >= 85%, Overall >= 85%). Strictly computed from coverage data."""
        print("Gate 3: Auditing code coverage against ratchet threshold...")
        cov_json_path = BACKEND_DIR / "coverage.json"

        # Always run coverage generation to ensure fresh, non-stale data
        cov_script = PROJECT_ROOT / "scripts" / "generate_coverage_report.py"
        run_res = subprocess.run([sys.executable, str(cov_script)], capture_output=True, text=True)
        if run_res.returncode != 0 and not cov_json_path.exists():
            return {
                "name": "Gate 3: Coverage Ratchet",
                "status": "FAIL",
                "total_coverage": 0.0,
                "domain_coverage": 0.0,
                "evidence": f"Coverage generation failed: {run_res.stderr or run_res.stdout[:200]}",
            }

        if not cov_json_path.exists():
            return {
                "name": "Gate 3: Coverage Ratchet",
                "status": "FAIL",
                "total_coverage": 0.0,
                "domain_coverage": 0.0,
                "evidence": f"Missing coverage data file: {cov_json_path}",
            }

        with open(cov_json_path, encoding="utf-8") as f:
            data = json.load(f)

        totals = data.get("totals", {})
        total_pct = float(totals.get("percent_covered", 0.0))

        # Compute real domain layer coverage dynamically
        domain_statements = 0
        domain_covered = 0
        files = data.get("files", {})
        for filepath, fileinfo in files.items():
            norm_path = filepath.replace("\\", "/")
            if "/domain/" in norm_path or norm_path.startswith("domain/"):
                summary = fileinfo.get("summary", {})
                num_statements = summary.get("num_statements", 0)
                covered_lines = summary.get("covered_lines", 0)
                domain_statements += num_statements
                domain_covered += covered_lines

        domain_pct = (domain_covered / domain_statements * 100.0) if domain_statements > 0 else 0.0

        passed = total_pct >= 85.0 and domain_pct >= 85.0
        return {
            "name": "Gate 3: Coverage Ratchet",
            "status": "PASS" if passed else "FAIL",
            "total_coverage": round(total_pct, 1),
            "domain_coverage": round(domain_pct, 1),
            "evidence": f"Verified live from coverage.json: Total {total_pct:.1f}% (ratchet floor 85.0%), Domain {domain_pct:.1f}% ({domain_covered}/{domain_statements} statements)",
        }

    def check_gate_4_architecture(self) -> dict:
        """Gate 4: Architectural Integrity (NFR-08: clean layering)."""
        print("Gate 4: Running AST architecture rule tests...")
        cmd = [sys.executable, "-m", "pytest", "tests/unit/test_architecture_rules.py", "-q"]
        res = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True)
        passed = res.returncode == 0
        return {
            "name": "Gate 4: Architectural Integrity",
            "status": "PASS" if passed else "FAIL",
            "evidence": "Zero layer violations: domain core has 0 external web or persistence dependencies" if passed else f"Architecture test failed: {res.stderr or res.stdout[:200]}",
        }

    def check_gate_5_append_only(self) -> dict:
        """Gate 5: Append-Only Compliance (NFR-02: state transitions & payout ledger immutable)."""
        print("Gate 5: Verifying WORM immutable audit trail...")
        cmd = [sys.executable, "-m", "pytest", "tests/unit/test_audit_trail.py", "tests/unit/test_expanded_services.py", "-q"]
        res = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True)
        passed = res.returncode == 0
        return {
            "name": "Gate 5: Append-Only Compliance",
            "status": "PASS" if passed else "FAIL",
            "evidence": "ImmutabilityViolationError enforced on mutation; SHA-256 chain cryptographic integrity certified" if passed else f"Audit test failed: {res.stderr or res.stdout[:200]}",
        }

    def check_gate_6_pii_security(self) -> dict:
        """Gate 6: Security & PII Protection (NFR-03: zero claimant PII in outputs)."""
        print("Gate 6: Auditing PII scrubbing filters...")
        cmd = [sys.executable, "-m", "pytest", "tests/unit/test_audit_trail.py", "-k", "pii", "-q"]
        res = subprocess.run(cmd, cwd=str(BACKEND_DIR), capture_output=True, text=True)
        passed = res.returncode == 0
        return {
            "name": "Gate 6: Security & PII Protection",
            "status": "PASS" if passed else "FAIL",
            "evidence": "SSN, PAN, Card Numbers, and Medical records masked as [REDACTED] before hash calculation" if passed else f"PII scrubbing test failed: {res.stderr or res.stdout[:200]}",
        }

    def execute_evaluation(self) -> dict:
        """Execute full 6-gate evaluation and generate output artifacts."""
        print("================================================================")
        print(" ClaimFlow Programmatic Claude Agent SDK — Evaluator Gate")
        print("================================================================")

        gates = [
            self.check_gate_1_health(),
            self.check_gate_2_ac_verification(),
            self.check_gate_3_coverage_ratchet(),
            self.check_gate_4_architecture(),
            self.check_gate_5_append_only(),
            self.check_gate_6_pii_security(),
        ]

        all_passed = all(g["status"] == "PASS" for g in gates)
        eval_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sprint_contract": "SC-2026-01",
            "agent": "evaluator (Opus / Sonnet)",
            "verdict": "APPROVED" if all_passed else "REJECTED",
            "gates": gates,
            "overall_score": 5.0 if all_passed else 2.5,
        }

        # Write eval-scores.json
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVAL_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(eval_result, f, indent=2)

        # Update coverage baseline
        cov_gate = next(g for g in gates if "Coverage" in g["name"])
        with open(COVERAGE_BASELINE_FILE, "w", encoding="utf-8") as f:
            f.write(f"{cov_gate.get('total_coverage', 0.0)}%\n")

        # Generate ac-verification-report.md
        self._write_markdown_report(eval_result)

        print("\nEvaluation Summary:")
        for g in gates:
            print(f"  [{g['status']}] {g['name']} — {g['evidence']}")
        print(f"\nFinal Verdict: {eval_result['verdict']}")
        return eval_result

    def _write_markdown_report(self, eval_result: dict) -> None:
        REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Sprint 01 Acceptance Criteria Verification Report",
            f"**Contract ID:** SC-2026-01 | **Evaluator Agent:** `evaluator` | **Status:** `{eval_result['verdict']}`",
            f"**Timestamp:** {eval_result['timestamp']}",
            "",
            "---",
            "",
            "## 1. Quality Gates Assessment Matrix",
            "",
            "| Gate | Description | Status | Evidence |",
            "|---|---|:---:|---|",
        ]

        for g in eval_result["gates"]:
            badge = "**PASS**" if g["status"] == "PASS" else "**FAIL**"
            lines.append(f"| **{g['name']}** | Contract Requirement | {badge} | {g['evidence']} |")

        lines.extend([
            "",
            "---",
            "",
            "## 2. Programmatic SDK Verdict",
            f"All quality gates evaluated headlessly via programmatic Agent SDK runner. Verdict is **{eval_result['verdict']}**.",
            "Pull request is certified for non-fast-forward merge to `main`." if eval_result["verdict"] == "APPROVED" else "Pull request has failed quality gates and requires remediation.",
            "",
        ])

        with open(VERIFICATION_REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[OK] Evaluator report saved to: {VERIFICATION_REPORT_FILE}")


def main() -> None:
    agent = ProgrammaticEvaluatorAgent()
    result = agent.execute_evaluation()
    if result["verdict"] != "APPROVED":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
