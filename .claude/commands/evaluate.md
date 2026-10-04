---
name: evaluate
description: Evaluates the live running application against the active sprint contract using three-layer verification (API checks, Playwright UI automation, schema validation).
argument-hint: "[group-id]"
agent: evaluator
---

# /evaluate — Application Evaluation & Contract Verification Command

When this command is invoked, the `evaluator` agent performs independent, skeptical verification of the running application against the active sprint contract, executing live API checks, Playwright browser interactions, and schema validations.

---

## Overview & Execution Context

- **Assigned Agent:** `evaluator` (`.claude/agents/evaluator.md`)
- **SDLC Gate:** Gate 5 (Runtime Contract & Quality Verification)
- **Input Dependencies:**
  - `sprint-contracts/{group}.json` (Verifiable done-criteria)
  - `project-manifest.json` (Service URLs and health check configurations)
  - `specs/design/api-contracts.schema.json` (OpenAPI schema for response validation)
- **Output Artifacts:**
  - `specs/reviews/evaluator-report.md` (Formal evaluation verdict and check inventory)
  - Updated `features.json` (Per-feature pass/fail status and failure telemetry)

---

## Non-Negotiable Evaluator Rules

1. **Execute Every Check:** Never skip a check because an adjacent check succeeded.
2. **Zero Rationalization:** If the contract expects HTTP 200 and the response is 201, 400, or 500, the check **FAILS**. Do not excuse failures as minor or expected.
3. **Evidence Over Opinion:** Every assertion must cite concrete data: exact status code, response body excerpt, server log snippet, or UI snapshot.
4. **Binary Scoring:** API and Playwright checks are strictly PASS or FAIL. No partial credit.
5. **Layer Ordering:** Execute Layer 1 (API) before Layer 2 (Playwright) before Layer 3 (Design).

---

## Execution Steps

### Step 1 — Load Evaluation Patterns & Schemas
- Read `.claude/skills/evaluation/SKILL.md` for project verification conventions.
- Confirm contract format adheres to `.claude/templates/sprint-contract.json`.

### Step 2 — Ingest Sprint Contract
Read `sprint-contracts/{group}.json` (e.g., `sprint-contracts/group-A.json`):
- Extract `api_checks`: HTTP endpoint verification definitions.
- Extract `playwright_checks`: Browser user interaction steps.
- Extract `design_checks`: Component and visual token assertions.
- Extract `architecture_checks`: Required files and schema rules.
- Extract `features`: Associated feature identifiers to update in `features.json`.

### Step 3 — Load Project Manifest & Runtime Endpoints
Read `project-manifest.json`:
- `api_base_url` (e.g., `http://localhost:8000`)
- `ui_base_url` (e.g., `http://localhost:3000`)
- `health_check` endpoint path (e.g., `/health`)

### Step 4 — Verify Application Stack Health
Execute health check retry loop against the running service:
```bash
curl --retry 5 --retry-delay 2 -sf {api_base_url}{health_check}
```
If the service is unreachable or returns non-200 after 5 retries:
- Immediately record an overall **FAIL** verdict.
- Set `failure_layer: "docker"` in `features.json`.
- Capture container logs (`docker compose logs --tail=50`) and halt further checks.

---

## Three-Layer Verification Protocol

### Layer 1 — API Verification Checks
For each check in `api_checks`:
1. Execute the HTTP request using `curl`:
   ```bash
   curl -s -w "\n%{http_code}" -X {method} "{api_base_url}{path}" \
     -H "Content-Type: application/json" \
     -d '{payload}'
   ```
2. Parse the output: separate the HTTP status code from the response body.
3. Verify status code equals `expect.status`.
4. Verify response body contains all required strings in `expect.body_contains`.
5. If `schema_ref` is provided, validate the JSON body against `specs/design/api-contracts.schema.json`.
6. On failure, extract the trailing 50 lines of server logs to provide root-cause diagnostic information.

### Layer 2 — Playwright UI Automation Checks
For each check in `playwright_checks`:
1. Launch browser interaction via Playwright MCP tools.
2. Navigate to target URL (`{ui_base_url}{path}`).
3. Interact using semantic locators:
   - Prefer `getByRole()`, `getByLabel()`, and `getByText()`.
   - CSS selectors and XPath are strictly prohibited.
4. Execute user actions (clicks, form fills, submissions).
5. Assert outcomes using `expect().toBeVisible()`.
   - **Banned:** Arbitrary timeouts (`waitForTimeout()`). If elements are not rendered within standard timeout, the check fails.
6. Capture DOM snapshot or screenshot evidence.

### Layer 3 — Design Critic Verification (Full Mode Only)
In Full execution mode:
- Delegate visual checks to the `design-critic` agent.
- Capture page snapshots at 1280px and 375px viewports.
- Record visual fidelity and token alignment scores against `calibration-profile.json`.

### Architecture Checks
Verify all file paths listed in `architecture_checks.files_must_exist`:
- Assert file existence on disk.
- Fail if any declared module, repository, or service file is missing.

---

## Step 5 — Update Feature Registry (`features.json`)

For every feature ID referenced in the sprint contract:
- Set `passes: true` if all related checks succeeded; otherwise `passes: false`.
- Record `last_evaluated` ISO 8601 timestamp.
- Record `failure_reason` describing the specific failed check.
- Record `failure_layer`: `"api"`, `"playwright"`, `"design"`, `"unit_test"`, or `"docker"`.

---

## Step 6 — Generate Evaluator Report

Write the evaluation verdict to `specs/reviews/evaluator-report.md`:
```markdown
# Evaluator Report — Group {group}

- **Date:** {Timestamp}
- **Verdict:** {PASS | FAIL}
- **Sprint Contract:** `sprint-contracts/{group}.json`

## API Checks
- [PASS] POST /api/v1/claims (Status: 201)
- [FAIL] GET /api/v1/claims/CLM-1001 (Expected: 200, Actual: 404)

## Playwright Checks
- [PASS] FNOL submission form renders with policy input
- [PASS] Document upload checklist visible

## Architecture Checks
- [PASS] All declared modules and interfaces present on disk

## Features Summary
- F001: PASS
- F002: FAIL (api: Expected status 200, received 404)
```

> [!IMPORTANT]
> The overall verdict is **PASS** if and only if **100% of all checks** across all layers succeed. A single check failure produces a **FAIL** verdict.
