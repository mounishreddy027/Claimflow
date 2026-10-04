---
name: test
description: Generates and executes test plans, test cases mapped to acceptance criteria, JSON fixtures, and Playwright E2E test suites.
argument-hint: "[--plan-only | --e2e-only]"
agent: test-engineer
---

# /test — Test Plan & Playwright E2E Generation Command

When this command is invoked, the `test-engineer` agent analyzes story acceptance criteria, generates a formal test plan, produces realistic domain fixtures, authors Playwright E2E suites, and executes validation checks across unit, integration, and UI layers.

---

## Overview & Execution Context

- **Assigned Agent:** `test-engineer` (`.claude/agents/test-engineer.md`)
- **SDLC Gate:** Verification & Quality Engineering
- **Invocation Flags:**
  - `/test`: End-to-end execution (generates test plan, fixtures, E2E specs, and runs suites).
  - `/test --plan-only`: Generates only test plan, test cases, and fixture definitions without generating E2E test code.
  - `/test --e2e-only`: Directly generates and executes Playwright E2E tests using existing test plans.
- **Output Artifacts:**
  - `specs/test_artefacts/test-plan.md` (Strategy, boundaries, and scope)
  - `specs/test_artefacts/test-cases.md` (Detailed test inventory mapped to AC-NN)
  - `specs/test_artefacts/test-data/*.json` (Realistic domain fixtures)
  - `e2e/{story-id}.spec.ts` (Playwright automated test suites)
  - `playwright.config.ts` (Playwright test runner configuration)

---

## Execution Steps

### Step 1 — Ingest Quality & Testing Guidelines
1. Read `.claude/skills/testing/SKILL.md` for multi-layer testing strategy:
   - **Layer 1 (Unit):** Isolated, in-memory, fast (< 10s total), mocking external boundaries only.
   - **Layer 2 (Integration):** Database and service interaction testing against real test containers.
   - **Layer 3 (E2E):** Complete user journeys via Playwright in browser environments.
2. Read `.claude/skills/code-gen/SKILL.md` for boundary value generation principles:
   - Empty inputs (zero, null, empty strings, empty collections).
   - Boundary limits (min, max, min - 1, max + 1).
   - Invalid formats and error paths.
   - Concurrency and race condition testing.

### Step 2 — Trace Acceptance Criteria
Read every story file in `specs/stories/` and extract:
- Functional Acceptance Criteria identifiers (`AC-01`, `AC-02`...).
- Non-Functional Requirements identifiers (`NFR-01` through `NFR-08`).
- Edge cases and error flows documented in each story.
- *Strict Rule:* Every generated test case must explicitly reference its canonical criterion ID.

### Step 3 — Generate Test Artefacts (`specs/test_artefacts/`)
Create `specs/test_artefacts/` and populate:

#### 1. `specs/test_artefacts/test-plan.md`
- **Scope & Objectives:** In-scope functional flows vs out-of-scope third-party boundaries.
- **Environment Assumptions:** Test database instance, seed policies, authentication tokens.
- **Pass/Fail Criteria:** 100% test pass rate, zero regression on existing suites.

#### 2. `specs/test_artefacts/test-cases.md`
- Test case identifier (`TC-{story}-{num}`).
- Linked Acceptance Criterion (`AC-NN` / `NFR-NN`).
- Preconditions, input test vectors, execution steps, expected outcomes.
- Explicit coverage for both happy paths and error paths (e.g., `PolicyNotActiveException`).

#### 3. `specs/test_artefacts/test-data/*.json`
- Generate realistic, domain-representative fixture data (e.g., `policies.json`, `claims.json`, `claimants.json`).
- Ensure valid UUIDs, realistic timestamps, plausible currency amounts, and consistent policy numbers.
- Placeholder text such as `"foo"`, `"test"`, or `123` is strictly prohibited.

---

### Step 4 — Author Playwright E2E Test Suites (`e2e/`)
For each story with `layer: UI` or end-to-end user workflows:
1. Generate `e2e/{story-id}.spec.ts`.
2. Configure `playwright.config.ts` using `.claude/templates/playwright.config.template.ts`.
3. Author tests enforcing strict locator standards:
   - Use semantic locators: `page.getByRole()`, `page.getByLabel()`, `page.getByText()`.
   - Never use brittle CSS selectors or XPath expressions.
   - Assert with auto-retrying expectations: `expect(locator).toBeVisible()`.
   - Banned: `page.waitForTimeout()`.
4. Follow Arrange → Act → Assert structure for every test block.

---

### Step 5 — Test Suite Execution & Coverage Verification

Execute the test suites and evaluate results:
```bash
# Backend unit & integration suite
pytest --cov=src --cov-report=term-missing -v   # or: npm test -- --coverage

# Playwright E2E suite (if application stack is active)
npx playwright test
```

**Coverage Verification Gate:**
- Compare total coverage against `.claude/state/coverage-baseline.txt`.
- Assert that coverage is **>= baseline** and **>= 80% (hard floor)**.
- If coverage drops or any test fails, record the diagnostic log and fail the command.
