# src/services/CLAUDE.md — Application Services Guidelines

This document governs the orchestration and application services layer (`src/services/`).

---

## 1. Service Responsibilities & Use Cases

Application services coordinate domain logic, persistence, and external stubs within transactional boundaries:

1. **`IntakeOrchestratorService`:**
   - Coordinates FNOL intake.
   - Loads policy and validates `PolicyActiveRule` (AC-02).
   - Initializes claim in `FILED` state (AC-01) and sets up document checklist (AC-03).
2. **`DocumentChecklistService`:**
   - Evaluates uploaded documents against line-of-business checklists (AC-03).
   - Transitions document status (`VERIFIED` / `REJECTED`).
   - Signals readiness for `UNDER_REVIEW`.
3. **`DeterministicFraudScreeningService`:**
   - Evaluates deterministic scoring rules [0–100] (AC-04).
   - Compares score to policy threshold.
   - Saves immutable fraud evaluation report (NFR-02).
4. **`AssessmentCalculationService`:**
   - Gathers claim and policy parameters.
   - Calls `AssessmentCalculator` to compute `payable_amount` with non-negative invariant (AC-05, NFR-01).
   - Persists assessment record (NFR-02).
5. **`SettlementLedgerService`:**
   - Evaluates decision criteria (AC-06).
   - Produces immutable payout record matching assessed amount (AC-07).
   - Advances state to `SETTLED` (AC-10).
6. **`DisputeReopenService`:**
   - Verifies claim is in `SETTLED` status.
   - Transitions parent claim to `REOPENED` (preserving queryability).
   - Spawns linked sub-claim entity (AC-08).
7. **`AdminOverrideService`:**
   - Enforces admin authority.
   - Applies decision override and logs audit trail with actor and timestamp (AC-09, NFR-04).

---

## 2. Transaction & Consistency Rules

- **Atomic Transactions:** State changes, payout writes, and audit logs within a use case must execute in a single atomic transaction.
- **Fail-Safe Rollbacks:** If an invariant fails (e.g., negative payable or illegal state jump), the entire transaction rolls back.
- **No Direct Domain Invariant Bypassing:** Services must delegate business rules and state changes to domain models rather than updating entity fields directly.
