# Sprint 02 Contract: Fraud Screening, Financial Assessment, Settlement & Reopen
## Contract ID: SC-2026-02 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Parties to Contract & Sprint Goal

- **Generator Agent:** `generator` (Sonnet) + Domain Teammates (`fraud-screening-agent`, `assessment-agent`, `settlement-agent`, `audit-tracer-agent`)
- **Evaluator Agent:** `evaluator` (Opus)
- **Sprint Goal:** Complete the claims lifecycle with deterministic fraud scoring, fixed-point financial assessment with non-negative invariant, automated/manual adjudication, immutable settlement payouts, sub-claim dispute reopening, and audited administrative overrides.

---

## 2. In-Scope Stories & Acceptance Criteria

| Story ID | Title & Scope | Primary AC | Target Verification Method |
|---|---|---|---|
| **STORY-201** | Deterministic Fraud Screening Engine | **AC-04** | Unit & Integration test: Deterministic scoring [0–100], policy version threshold check. |
| **STORY-202** | Fixed-Point Assessment Calculator | **AC-05** | Unit test: `payable = min(claim, sum_insured) - deductibles - co_pay`; verify invariant `payable >= 0` and `BigDecimal` precision (**NFR-01**). |
| **STORY-203** | Adjudication Decision Engine | **AC-06** | Unit test: `AUTO_APPROVE`, `MANUAL_REVIEW`, `REJECT` decisions with versioned policy reason codes. |
| **STORY-204** | Immutable Settlement & Payout Generation | **AC-07** | Integration test: Immutable payout record generated matching assessed amount (**NFR-02**). |
| **STORY-205** | Dispute Sub-Claim Reopening | **AC-08** | API test: Dispute transitions claim to `REOPENED`, spawns linked sub-claim, keeps history queryable. |
| **STORY-206** | Audited Admin Decision Override | **AC-09** | API & Auth test: `ROLE_ADMIN` overrides decision with reason code and comment; audit verified (**NFR-04**). |

---

## 3. Evaluator Quality Gates & Definition of Done

The `evaluator` will approve the sprint and permit ratcheting if and only if **all 7 gates** PASS:

1. **Gate 1: Service Health & Liveness:**
   - Cold startup responds within 1,000ms (**NFR-07**).
2. **Gate 2: Acceptance Criteria Verification:**
   - 100% of scenarios in `specs/fraud_screening_spec.md`, `specs/assessment_spec.md`, `specs/settlement_spec.md`, `specs/reopen_spec.md`, and `specs/admin_override_spec.md` pass.
   - All tests tagged with `@tag("AC-04")` through `@tag("AC-09")`.
3. **Gate 3: Financial Invariant & Precision Verification:**
   - Zero occurrences of `float`/`double` in financial calculations (**NFR-01**).
   - Invariant test suite confirms `payable_amount >= 0.00` across 1,000 boundary permutations.
   - Payout amount equality invariant verified: `payout_amount == payable_amount`.
4. **Gate 4: Immutability & Append-Only Verification:**
   - Attempted `UPDATE` or `DELETE` on payout records or audit logs fails at database constraint level (**NFR-02**).
5. **Gate 5: Role-Based Access Control Verification:**
   - Assessor cannot invoke admin override endpoint (returns 403) (**NFR-04**).
6. **Gate 6: Code Coverage Ratchet:**
   - Overall repository test coverage reaches ≥ **88%** (domain layer ≥ **92%**).
7. **Gate 7: UI Workflow Validation (Playwright MCP):**
   - Playwright browser tests successfully simulate claimant FNOL filing, assessor workbench decisioning, and admin override view.

---

## 4. Contract Sign-Off

- **Generator Commitment:** *"I commit to delivering the complete financial assessment, fraud, settlement, and override logic adhering strictly to fixed-point precision, immutability, and AC-04 through AC-09."*
- **Evaluator Criteria:** *"I will objectively test boundary conditions, stress-test the payable non-negative invariant, audit role boundaries, and verify Playwright browser interactions before approving PR merge."*
