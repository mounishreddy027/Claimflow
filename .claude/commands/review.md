---
name: review
description: Executes comprehensive code quality, OWASP Top 10 security auditing, and architecture drift checks by coordinating evaluator and security-reviewer agents.
argument-hint: "[story-id-or-group-id]"
agent: security-reviewer
---

# /review — Code Quality & Security Review Command

When this command is invoked, the `security-reviewer` and `evaluator` agents are spawned concurrently to execute a comprehensive quality and security audit covering OWASP Top 10 vulnerabilities, architecture drift, PII leaks, RBAC boundaries, and sprint contract satisfaction.

---

## Overview & Execution Context

- **Primary Agents:** `security-reviewer` (`.claude/agents/security-reviewer.md`) and `evaluator` (`.claude/agents/evaluator.md`)
- **SDLC Gate:** Pre-Merge Quality & Compliance Gate
- **Invocation Scope:** Current working tree changes, specific story, or completed dependency group
- **Output Artifacts:**
  - `specs/reviews/security-review.md` (Security findings and vulnerability analysis)
  - `specs/reviews/evaluator-report.md` (Contract verification and feature states)

---

## Execution Steps

### Step 1 — Concurrent Agent Execution
Launch both specialized review agents concurrently in a single operation:

```
┌────────────────────────────────────────────────────────┐
│                   /review Invocation                   │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       (Concurrent Audit)       (Concurrent Audit)
                │                        │
                ▼                        ▼
     ┌──────────────────────┐ ┌──────────────────────┐
     │  security-reviewer   │ │      evaluator       │
     │                      │ │                      │
     │ - OWASP Top 10       │ │ - API checks         │
     │ - PII log redaction  │ │ - Playwright UI E2E  │
     │ - RBAC boundaries    │ │ - Architecture rules │
     │ - Secret detection   │ │ - Contract alignment │
     └──────────┬───────────┘ └──────────┬───────────┘
                │                        │
                ▼                        ▼
      security-review.md        evaluator-report.md
```

#### 1. Security Reviewer Responsibilities
The `security-reviewer` agent audits all modified and generated files against:
- **Injection Flaws:** SQL injection, command injection, and unsanitized template interpolation. Check ORM parameter binding and raw queries.
- **Authentication & RBAC Boundaries (NFR-04):** Ensure `/api/v1/admin/**` endpoints are strictly protected by role checks and verify assessor vs admin role isolation.
- **PII Leakage Prevention (NFR-03):** Verify health records, claim narratives, and claimant personal information are excluded from application logs.
- **Secret Detection:** Scan for hardcoded credentials, API keys, private certificates, and insecure JWT tokens.
- **Input Validation & Deserialization:** Verify request models enforce bounds on numerical values and string lengths.

#### 2. Evaluator Responsibilities
The `evaluator` agent runs runtime verification against the running application:
- Executes all HTTP `api_checks` from the active sprint contract.
- Executes Playwright automated interaction sequences for UI stories.
- Verifies that all expected architectural files are present on disk.
- Updates `features.json` with resulting verdicts.

---

### Step 2 — Architecture Drift & Layering Review
Verify that production code complies with the project's strict layered architecture:
- Controllers / API layer depends only on Service layer.
- Service layer depends only on Repository and Domain layers.
- Domain layer remains pure with zero dependencies on database drivers or web frameworks.
- Financial computations strictly use fixed-point arithmetic (`BigDecimal` / `decimal`) to satisfy **NFR-01**.
- Append-only storage guarantees (**NFR-02**): Verify that financial, claim, and assessment tables contain zero `UPDATE` or `DELETE` statements.

---

### Step 3 — Findings Classification & Severity Triage

Classify all detected issues into standard severity levels:

| Severity | Definition | Action Required |
|---|---|---|
| **BLOCK** | Critical security flaw, broken contract, failing test, PII leak, or architectural boundary violation. | Blocks PR/merge. Triggers self-healing loop. |
| **WARN** | Sub-optimal performance, missing index, or non-critical formatting inconsistency. | Documented in review report; does not block merge. |
| **INFO** | Advisory code simplification or modernization note. | Optional backlog improvement. |

---

### Step 4 — Self-Healing Loop for BLOCK Findings

If one or more **BLOCK** findings are identified:
1. Aggregate the BLOCK findings with file path, line numbers, and error descriptions.
2. Spawn the `generator` agent with instructions to remediate the specific defects without introducing unrelated functionality.
3. Re-run `/review` upon fix completion to verify resolution.
4. **Retry Threshold:** Allow up to **3 remediation cycles**. If BLOCK findings remain unresolved after 3 attempts, escalate the full audit report to the human engineer.

---

### Step 5 — Output Artifacts

Write findings to disk under `specs/reviews/`:
- **`specs/reviews/security-review.md`:** Detailed security findings, vulnerability classifications, affected line numbers, and remediation guidance.
- **`specs/reviews/evaluator-report.md`:** Runtime pass/fail verification matrix.

> [!CAUTION]
> A sprint or feature group is not ready for merge until `security-review.md` contains **0 BLOCK findings** and `evaluator-report.md` shows an overall **PASS** verdict.
