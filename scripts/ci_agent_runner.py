#!/usr/bin/env python3
"""
scripts/ci_agent_runner.py — Headless CI Agent Runner & Evaluation Orchestrator

Invoked within CI pipelines (.github/workflows/ci.yml) to execute:
1. Architectural integrity checks & AST inspections
2. Automated coverage generation & ratchet enforcement
3. Live background server management for HTTP health probe
4. Programmatic Claude Agent SDK evaluator quality gates
5. Acceptance criteria sign-off artifact generation (ac-verification-report.md)
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def log_ci(title: str, message: str, level: str = "notice") -> None:
    """Output formatted logs, emitting GitHub Actions workflow syntax if in CI."""
    is_github_actions = "GITHUB_ACTIONS" in os.environ
    if is_github_actions:
        print(f"::{level} title={title}::{message}")
    print(f"[{level.upper()}] {title}: {message}")


def is_port_responding(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CI-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status in (200, 304)
    except Exception:
        return False


def run_command(cmd: list[str], cwd: Path, step_name: str) -> bool:
    """Run a CLI command with group headers and error checking."""
    is_github_actions = "GITHUB_ACTIONS" in os.environ
    if is_github_actions:
        print(f"::group::{step_name}")
    else:
        print(f"\n--- {step_name} ---")

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd))

    if is_github_actions:
        print("::endgroup::")

    if result.returncode != 0:
        log_ci(step_name, f"Failed with exit code {result.returncode}", level="error")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="ClaimFlow Headless CI Agent Runner")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running pytest suite")
    parser.add_argument("--strict", action="store_true", default=True, help="Fail on any gate violation")
    parser.add_argument("--coverage-ratchet", type=float, default=85.0, help="Minimum required coverage percentage")
    args = parser.parse_args()

    print("=================================================================")
    print(" ClaimFlow Autonomous CI Agent Runner (Claude Harness Framework)")
    print("=================================================================")

    # Step 1: Run Architecture Rules & Lint Checks
    arch_cmd = [sys.executable, "-m", "pytest", "tests/unit/test_architecture_rules.py", "-q"]
    if not run_command(arch_cmd, BACKEND_DIR, "Architecture Layering & Immutability Rules"):
        return 1

    # Step 2: Generate Coverage & Verification Report
    cov_cmd = [sys.executable, str(SCRIPTS_DIR / "generate_coverage_report.py")]
    if not run_command(cov_cmd, PROJECT_ROOT, "Coverage Generation & Ratchet Audit"):
        return 1

    # Step 3: Ensure Backend Server is Running for Live HTTP Health Probe
    backend_proc = None
    health_url = "http://127.0.0.1:8000/health"
    if not is_port_responding(health_url):
        print(f"\nStarting live Backend server for Evaluator Gate 1 probe...")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "claimflow.main:app", "--host", "127.0.0.1", "--port", "8000", "--app-dir", "src"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(20):
            time.sleep(0.5)
            if is_port_responding(health_url):
                print(f"[OK] Backend responding at {health_url}")
                break

    try:
        # Step 4: Run Programmatic Evaluator SDK against live HTTP server
        sdk_cmd = [sys.executable, str(SCRIPTS_DIR / "run_evaluator_sdk.py")]
        if not run_command(sdk_cmd, PROJECT_ROOT, "Claude Agent Evaluator 6-Gate Verification"):
            return 1
    finally:
        if backend_proc:
            backend_proc.terminate()

    log_ci("CI Gate Complete", "All architectural, quality, and AC gates verified successfully!", level="notice")
    return 0


if __name__ == "__main__":
    sys.exit(main())
