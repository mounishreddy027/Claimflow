# src/domain/CLAUDE.md — Domain Layer Engineering Guidelines

This document governs the innermost core domain layer (`src/domain/`).

---

## 1. Core Principles: Purity & Zero Dependencies

The domain layer contains the enterprise business rules and entities.
- **Zero Framework Annotations:** No framework dependencies (no Spring Web/JPA, no Express/TypeORM, no FastAPI/Pydantic-ORM specifics).
- **Zero I/O:** Domain entities, rules, and value objects must not execute file, network, or database I/O.
- **Fail Fast on Invariants:** Invariants are asserted inside constructors, factories, and domain transition methods.

---

## 2. Domain Packages & Components

1. **`models/`:**
   - `Claim`: Aggregate root tracking claim identity, policy reference, incident date, amounts, and state transitions.
   - `Policy`: Value object representing policy coverage limits, effective start/end dates, deductible, co-pay, fraud threshold, and version.
   - `Document`: Entity tracking uploaded document type, verification status (`PENDING`, `VERIFIED`, `REJECTED`), and review notes.
   - `Assessment`: Immutable record capturing calculated effective claim, deductions, and final payable amount.
   - `PayoutRecord`: Immutable record holding payout amount, settlement timestamp, and status.
2. **`rules/`:**
   - `PolicyActiveRule` (AC-02): Validates `policy.isActiveOn(incidentDate)`; raises `PolicyNotActiveException` if false.
   - `DocumentChecklistRule` (AC-03): Enforces required document types per `ClaimType` (`MOTOR`, `HEALTH`, `LIFE`).
   - `FraudScoringRule` (AC-04): Executes deterministic scoring [0–100]; compares to policy threshold.
   - `AssessmentCalculator` (AC-05): Computes `payable = min(claim, sum_insured) - deductibles - co_pay`; enforces `payable >= 0`.
3. **`state/`:**
   - `ClaimStateMachine` (AC-10): Enforces transitions: `FILED` → `UNDER_REVIEW` → `APPROVED`/`REJECTED` → `SETTLED` → `REOPENED`.
   - Any invalid transition raises `InvalidClaimStateException`.
4. **`valueobjects/`:**
   - `FixedPointMoney` (NFR-01): Immutable wrapper around `BigDecimal` enforcing 2 decimal places and `HALF_EVEN` rounding.

---

## 3. Mandatory Invariants

- Invariant 1: `payable_amount >= 0.00` always holds (AC-05).
- Invariant 2: `payout_amount == payable_amount` strictly holds (AC-07).
- Invariant 3: Payout and assessment amounts can never be mutated once finalized (NFR-02).
- Invariant 4: No floating-point types (`float`, `double`) are permitted in this package.
