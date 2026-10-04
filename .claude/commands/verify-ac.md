---
name: verify-ac
description: Verifies end-to-end alignment and test coverage for all Functional Acceptance Criteria (AC-01 through AC-10) and Non-Functional Requirements (NFR-01 through NFR-08).
---

# /verify-ac — Acceptance Criteria Verification Command

When this command is invoked, the agent orchestrates a full audit across specifications, domain rules, and test suites.

## Execution Steps

### 1. Specification & Criteria Discovery
Scan `specs/` and verify that every canonical Acceptance Criterion has an explicit section:
- `AC-01`: FNOL submission in `specs/intake_spec.md`
- `AC-02`: Policy active check in `specs/intake_spec.md`
- `AC-03`: Document checklists in `specs/document_verification_spec.md`
- `AC-04`: Fraud scoring in `specs/fraud_screening_spec.md`
- `AC-05`: Assessment math in `specs/assessment_spec.md`
- `AC-06`: Decision engine in `specs/settlement_spec.md`
- `AC-07`: Immutable payout in `specs/settlement_spec.md`
- `AC-08`: Dispute & sub-claim in `specs/reopen_spec.md`
- `AC-09`: Admin override in `specs/admin_override_spec.md`
- `AC-10`: State transitions in `specs/state_machine_spec.md`

### 2. Test Tag Auditing
Scan `tests/` to verify that each AC and NFR has at least one corresponding test referencing its identifier:
```bash
grep -rn "AC-01" tests/
grep -rn "AC-02" tests/
grep -rn "AC-03" tests/
grep -rn "AC-04" tests/
grep -rn "AC-05" tests/
grep -rn "AC-06" tests/
grep -rn "AC-07" tests/
grep -rn "AC-08" tests/
grep -rn "AC-09" tests/
grep -rn "AC-10" tests/
grep -rn "NFR-01" tests/
grep -rn "NFR-08" tests/
```

### 3. Generate Verification Report
Produce `specs/reviews/ac-verification-report.md` detailing:
- Status per AC (PASS / FAIL / PENDING)
- Test file mapping
- Invariant compliance check
