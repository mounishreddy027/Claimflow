# .claude/hooks/README.md — ClaimFlow Substrate Hook Specifications

This document defines the project-specific enforcement hooks designed to run at pre-commit, post-write, and evaluation gates within the Claude Harness Engine substrate.

---

## 1. Project-Specific Hooks Overview

| Hook Name | Target Scope | Trigger Event | Primary Requirement Enforced |
|---|---|---|---|
| **`payout-invariant-check`** | `src/domain/`, `specs/assessment_spec.md` | Post-Write / Pre-Commit | Enforces **AC-05** and **NFR-01**: Invariant $\text{payable\_amount} \ge 0$ holds and no floating-point arithmetic is present. |
| **`pii-redaction-check`** | `src/controllers/`, log output | Pre-Commit / Ratchet Gate | Enforces **NFR-03**: Scans for unmasked claimant SSN, diagnoses, or account credentials in log formats. |
| **`claim-immutability-check`** | `src/repositories/`, SQL migrations | Pre-Commit | Enforces **NFR-02**: Blocks any code path attempting direct SQL `UPDATE` or `DELETE` on financial ledgers. |

---

## 2. Hook Specifications & Logic

### 2.1 Hook: `payout-invariant-check`
- **Purpose:** Verifies that all financial calculation functions explicitly check or enforce non-negative boundaries and fixed-point data types.
- **Specification:**
  - Scans changed files in `src/domain/`.
  - Greps for prohibited floating-point primitives: `float`, `double`, `Float`, `Double`.
  - Asserts that `AssessmentCalculator` contains explicit clamping `max(BigDecimal.ZERO, ...)` or conditional boundary checks.
  - Exit code `0` on compliance; exit code `1` (blocking write) on violation.

### 2.2 Hook: `pii-redaction-check`
- **Purpose:** Prevents accidental logging of sensitive policyholder data in controller and service layers.
- **Specification:**
  - Scans log statements across `src/controllers/` and `src/services/`.
  - Detects raw logging of sensitive entity properties: `claimant.ssn`, `claimant.diagnosis`, `claimant.bankAccount`, `intakeRequest.toString()`.
  - Verifies presence and binding of `PiiRedactionFilter`.
  - Exit code `0` on clean logs; exit code `1` with warning diagnostics on detected leakage.

### 2.3 Hook: `claim-immutability-check`
- **Purpose:** Ensures database repositories adhere strictly to append-only semantics.
- **Specification:**
  - Inspects query strings and repository methods for `payout_records`, `assessments`, `fraud_evaluations`, and `claims`.
  - Blocks SQL patterns containing `UPDATE payout_records`, `DELETE FROM claims`, etc.
  - Enforces that state changes route through `claim_state_transitions` insertions.
