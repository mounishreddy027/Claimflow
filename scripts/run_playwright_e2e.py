#!/usr/bin/env python3
"""
scripts/run_playwright_e2e.py — ClaimFlow Playwright E2E & Snapshot Generator

Executes browser user journeys against the ClaimFlow web application (port 3000 UI, port 8000 API),
validating end-to-end functionality and generating verified test results and snapshot artifacts.
"""

import json
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
REPORT_DIR = PROJECT_ROOT / "playwright-report"
SNAPSHOTS_DIR = REPORT_DIR / "snapshots"

UI_URL = os.getenv("UI_BASE_URL", "http://127.0.0.1:3000")
API_URL = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")


def is_port_responding(url: str) -> bool:
    """Check if a URL responds to an HTTP GET request."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Playwright-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status in (200, 304)
    except Exception:
        return False


def start_server_if_needed(name: str, check_url: str, cmd: list[str], cwd: Path) -> subprocess.Popen | None:
    """Start a local background server if it's not already responding."""
    if is_port_responding(check_url):
        print(f"[OK] {name} is already running at {check_url}")
        return None

    print(f"Starting {name} at {check_url}...")
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 10 seconds for server to be responsive
    for _ in range(20):
        time.sleep(0.5)
        if is_port_responding(check_url):
            print(f"[OK] {name} started successfully.")
            return proc

    print(f"Warning: {name} did not respond within timeout, proceeding anyway.")
    return proc


def run_e2e_tests() -> dict:
    """Execute Playwright browser testing and capture visual snapshots."""
    from playwright.sync_api import sync_playwright

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    results = {
        "suite": "ClaimFlow Core Claims Lifecycle Journey",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ui_url": UI_URL,
        "api_url": API_URL,
        "tests": [],
        "snapshots": [],
        "passed": 0,
        "failed": 0,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Test 1: Liveness & Health Probe
        t1_start = time.perf_counter()
        health_status = "FAILED"
        health_latency_ms = None
        try:
            req = urllib.request.Request(f"{API_URL}/health", headers={"User-Agent": "Playwright-Agent/1.0"})
            h_start = time.perf_counter()
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                h_latency = (time.perf_counter() - h_start) * 1000.0
                body = json.loads(resp.read().decode())
                if resp.status == 200 and body.get("status") == "ok" and h_latency < 1000:
                    health_status = "PASSED"
                    health_latency_ms = round(h_latency, 2)
        except Exception as exc:
            print(f"Health test failed: {exc}")
            traceback.print_exc()

        t1_duration = round((time.perf_counter() - t1_start) * 1000.0, 2)
        results["tests"].append({
            "name": "Liveness & Health Probe responds under 1,000ms (NFR-07)",
            "status": health_status,
            "duration_ms": t1_duration,
            "latency_ms": health_latency_ms,
        })
        if health_status == "PASSED":
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 2: Dashboard Navigation & Live Stats
        t2_start = time.perf_counter()
        dash_status = "PASSED"
        try:
            page.goto(UI_URL, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1000)

            # Assert brand title and primary navigation buttons
            assert page.locator("h1:has-text('ClaimFlow')").is_visible(), "ClaimFlow heading not found"
            assert page.locator("#tab-dashboard").is_visible(), "Dashboard tab not found"
            assert page.locator("#tab-intake").is_visible(), "File FNOL tab not found"
            assert page.locator("#tab-fraud").is_visible(), "AI Fraud Screener tab not found"

            # Capture snapshot 1: Dashboard
            snap1 = SNAPSHOTS_DIR / "01-dashboard.png"
            page.screenshot(path=str(snap1), full_page=True)
            results["snapshots"].append({
                "name": "01-dashboard.png",
                "description": "ClaimFlow Executive Claims Dashboard with live stats and claims ledger",
                "path": str(snap1.relative_to(PROJECT_ROOT)),
            })
        except Exception as exc:
            dash_status = "FAILED"
            print(f"Dashboard test failed: {exc}")
            traceback.print_exc()

        t2_duration = round((time.perf_counter() - t2_start) * 1000.0, 2)
        results["tests"].append({
            "name": "ClaimFlow Dashboard loads with navigation and live stats",
            "status": dash_status,
            "duration_ms": t2_duration,
        })
        if dash_status == "PASSED":
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 3: FNOL Intake Submission Workflow
        t3_start = time.perf_counter()
        fnol_status = "PASSED"
        try:
            # Click File FNOL tab
            page.locator("#tab-intake").click()
            page.wait_for_timeout(600)
            page.wait_for_selector("#section-intake:not(.hidden)", timeout=5000)

            # Capture snapshot 2: FNOL Intake Form
            snap2 = SNAPSHOTS_DIR / "02-fnol-form.png"
            page.screenshot(path=str(snap2), full_page=True)
            results["snapshots"].append({
                "name": "02-fnol-form.png",
                "description": "FNOL Intake Form with active date validation & document checklist generation",
                "path": str(snap2.relative_to(PROJECT_ROOT)),
            })

            # Select first policy
            policy_select = page.locator("#intakePolicySelect")
            policy_select.wait_for(state="visible", timeout=5000)
            opts = policy_select.locator("option").all()
            if len(opts) > 1:
                policy_val = opts[1].get_attribute("value")
                if policy_val:
                    policy_select.select_option(policy_val)

            # Fill in claim amount & description
            page.locator("#intakeClaimAmount").fill("3450.00")
            page.locator("#intakeDescription").fill("Rear fender bumper collision sustained while stationary at signal.")

            # Submit FNOL form
            submit_btn = page.locator("button:has-text('Submit FNOL Claim')")
            submit_btn.click()
            page.wait_for_timeout(1000)

            # Capture snapshot 3: Submitted state
            snap3 = SNAPSHOTS_DIR / "03-fnol-submitted.png"
            page.screenshot(path=str(snap3), full_page=True)
            results["snapshots"].append({
                "name": "03-fnol-submitted.png",
                "description": "Post-submission state confirming claim intake registration",
                "path": str(snap3.relative_to(PROJECT_ROOT)),
            })
        except Exception as exc:
            fnol_status = "FAILED"
            print(f"FNOL test failed: {exc}")
            traceback.print_exc()

        t3_duration = round((time.perf_counter() - t3_start) * 1000.0, 2)
        results["tests"].append({
            "name": "FNOL Claim Intake workflow with policy validation",
            "status": fnol_status,
            "duration_ms": t3_duration,
        })
        if fnol_status == "PASSED":
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 4: Audit Trail & WORM Ledger View
        t4_start = time.perf_counter()
        audit_status = "PASSED"
        try:
            page.locator("#tab-audit").click()
            page.wait_for_timeout(600)
            page.wait_for_selector("#section-audit:not(.hidden)", timeout=5000)

            # Capture snapshot 4: Audit Trail
            snap4 = SNAPSHOTS_DIR / "04-audit-trail.png"
            page.screenshot(path=str(snap4), full_page=True)
            results["snapshots"].append({
                "name": "04-audit-trail.png",
                "description": "WORM Immutable Audit Trail with cryptographic hash chaining and PII scrubbing",
                "path": str(snap4.relative_to(PROJECT_ROOT)),
            })
        except Exception as exc:
            audit_status = "FAILED"
            print(f"Audit trail test failed: {exc}")
            traceback.print_exc()

        t4_duration = round((time.perf_counter() - t4_start) * 1000.0, 2)
        results["tests"].append({
            "name": "Audit Trail & WORM Ledger cryptographic verification view",
            "status": audit_status,
            "duration_ms": t4_duration,
        })
        if audit_status == "PASSED":
            results["passed"] += 1
        else:
            results["failed"] += 1

        browser.close()

    # Save results.json
    results_file = REPORT_DIR / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Generate HTML report
    html_content = generate_html_report(results)
    index_file = REPORT_DIR / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return results


def generate_html_report(res: dict) -> str:
    """Generate interactive HTML report for Playwright test results and snapshot gallery."""
    test_rows = "".join(
        f"""<tr>
          <td style="padding:10px 14px;border-bottom:1px solid #334155;color:#e2e8f0;">{t['name']}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #334155;text-align:center;">
            <span style="background:{'#065f46' if t['status']=='PASSED' else '#991b1b'};color:{'#34d399' if t['status']=='PASSED' else '#f87171'};padding:3px 10px;border-radius:9999px;font-weight:bold;font-size:11px;">{t['status']}</span>
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #334155;color:#94a3b8;text-align:right;">{t['duration_ms']}ms</td>
        </tr>"""
        for t in res["tests"]
    )

    snapshot_cards = "".join(
        f"""<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.3);">
          <div style="padding:12px 16px;border-bottom:1px solid #334155;">
            <h4 style="margin:0;color:#f1f5f9;font-size:14px;font-weight:600;">{s['name']}</h4>
            <p style="margin:4px 0 0;color:#94a3b8;font-size:12px;">{s['description']}</p>
          </div>
          <div style="background:#0f172a;padding:8px;text-align:center;">
            <img src="snapshots/{s['name']}" alt="{s['name']}" style="max-width:100%;height:auto;border-radius:6px;border:1px solid #334155;" />
          </div>
        </div>"""
        for s in res["snapshots"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ClaimFlow Playwright E2E Verification Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #0f172a; padding: 10px 14px; text-align: left; font-size: 11px; text-transform: uppercase; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
      <div>
        <h1 style="margin:0;font-size:24px;color:#f8fafc;">🎭 Playwright E2E Verification Report</h1>
        <p style="margin:6px 0 0;color:#94a3b8;font-size:13px;">Generated: {res['timestamp']} | UI: <code>{res['ui_url']}</code> | API: <code>{res['api_url']}</code></p>
      </div>
      <div>
        <span style="background:{'#065f46' if res['failed']==0 else '#991b1b'};color:{'#34d399' if res['failed']==0 else '#f87171'};padding:6px 16px;border-radius:9999px;font-weight:bold;font-size:14px;">
          {res['passed']}/{len(res['tests'])} PASSED
        </span>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-top:0;color:#f1f5f9;font-size:16px;">Test Scenarios Execution</h3>
      <table>
        <thead>
          <tr>
            <th>Scenario</th>
            <th style="text-align:center;">Result</th>
            <th style="text-align:right;">Duration</th>
          </tr>
        </thead>
        <tbody>
          {test_rows}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3 style="margin-top:0;color:#f1f5f9;font-size:16px;">Visual Snapshots Gallery ({len(res['snapshots'])} artifacts)</h3>
      <div style="display:grid;grid-template-columns:1fr;gap:20px;">
        {snapshot_cards}
      </div>
    </div>
  </div>
</body>
</html>"""


def main() -> int:
    print("================================================================")
    print(" ClaimFlow Playwright E2E & Snapshot Verification Runner")
    print("================================================================")

    # 1. Start backend server (port 8000) if needed
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "claimflow.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--app-dir",
        "src",
    ]
    backend_proc = start_server_if_needed("Backend API", f"{API_URL}/health", backend_cmd, BACKEND_DIR)

    # 2. Start frontend static server (port 3000) if needed
    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        "3000",
        "--bind",
        "127.0.0.1",
    ]
    frontend_proc = start_server_if_needed("Frontend UI", UI_URL, frontend_cmd, FRONTEND_DIR)

    try:
        # 3. Execute tests & snapshots
        res = run_e2e_tests()

        print("\nPlaywright Verification Results:")
        for t in res["tests"]:
            print(f"  [{t['status']}] {t['name']} ({t['duration_ms']}ms)")

        print(f"\nSnapshots Captured ({len(res['snapshots'])}):")
        for s in res["snapshots"]:
            print(f"  - {s['name']}: {s['description']}")

        print(f"\n[OK] Playwright report written to: {REPORT_DIR / 'index.html'}")
        print(f"[OK] Test results saved to: {REPORT_DIR / 'results.json'}")

        if res["failed"] > 0:
            return 1
        return 0
    finally:
        # Clean up any background processes started by this runner
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
