# Sprint 01 Contract: Core Intake, Document Verification & State Machine
## Contract ID: SC-2026-01 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Parties to Contract & Sprint Goal

- **Generator Agent:** `generator` (Sonnet) + Domain Teammates (`claim-intake-agent`, `state-machine-validator-agent`)
- **Evaluator Agent:** `evaluator` (Opus)
- **Sprint Goal:** Establish the foundational claims intake pipeline, policy temporal validation, claim-type document checklists, and the core claim lifecycle state machine.

---

## 2. In-Scope Stories & Acceptance Criteria

| Story ID | Title & Scope | Primary AC | Target Verification Method |
|---|---|---|---|
| **STORY-101** | FNOL Submission Endpoint & Validation | **AC-01** | API test: POST `/api/v1/claims/intake` returns 201 with claim reference. |
| **STORY-102** | Policy Active Temporal Validation | **AC-02** | Unit & API test: Throws `PolicyNotActiveException` if policy inactive on incident date. |
| **STORY-103** | Document Checklist Verification Engine | **AC-03** | Unit test: Enforce checklists for Motor (FIR+Invoice), Health (Bill+Summary), Life (Cert). |
| **STORY-104** | Claim Lifecycle State Machine Core | **AC-10** | Exhaustive matrix unit test: Verify valid transitions and `InvalidClaimStateException`. |

---

## 3. Evaluator Quality Gates & Definition of Done

The `evaluator` will approve the sprint and permit ratcheting if and only if **all 6 gates** PASS:

1. **Gate 1: Service Health & Startup:**
   - Application boots cleanly; `GET /health` returns HTTP 200 with latency < 1,000ms (**NFR-07**).
2. **Gate 2: Acceptance Criteria Verification:**
   - 100% of test scenarios defined in `specs/intake_spec.md`, `specs/document_verification_spec.md`, and `specs/state_machine_spec.md` pass without failure.
   - All tests tagged with `@tag("AC-01")`, `@tag("AC-02")`, `@tag("AC-03")`, `@tag("AC-10")`.
3. **Gate 3: Coverage Ratchet:**
   - Code coverage across `src/domain/` reaches at least **85%** (hard floor 80%).
4. **Gate 4: Architectural Integrity:**
   - Zero violations in `ArchUnit` / structural tests (**NFR-08**).
   - Domain layer has zero dependencies on controllers or persistence frameworks.
5. **Gate 5: Append-Only Compliance:**
   - State machine transition history verified as append-only (**NFR-02**).
6. **Gate 6: Security & PII Protection:**
   - Zero claimant PII written to log outputs (**NFR-03**).

---

## 4. Contract Sign-Off

- **Generator Commitment:** *"I commit to generating pure, surgical code satisfying AC-01, AC-02, AC-03, and AC-10 via TDD without hand-coding."*
- **Evaluator Criteria:** *"I will objectively test the running container, inspect logs for PII, and verify all state transitions before stamping PASS."*
