---
name: state-machine-validator
description: Validates claim lifecycle state transitions and verifies InvalidClaimStateException on illegal paths (AC-10).
---

# State Machine Validator Skill

This skill enforces finite state machine integrity and validates error handling for illegal lifecycle transitions in compliance with **AC-10**.

---

## 1. When to Use This Skill
- Designing, testing, or reviewing `ClaimStateMachine`.
- Verifying service-level state transitions.
- Writing test cases for invalid state paths.

---

## 2. Permitted Transition Table

```
+---------------+-------------------+------------------------------------------+
| Current State | Permitted Targets | Triggering Context                       |
+---------------+-------------------+------------------------------------------+
| NONE          | FILED             | FNOL Submission                          |
| FILED         | UNDER_REVIEW      | Document Checklist Complete (AC-03)      |
| UNDER_REVIEW  | APPROVED          | Assessment Complete & Approved (AC-06)   |
| UNDER_REVIEW  | REJECTED          | Claim Rejected (AC-06)                   |
| APPROVED      | SETTLED           | Immutable Payout Disbursed (AC-07)       |
| APPROVED      | REJECTED          | Admin Override (AC-09)                   |
| REJECTED      | APPROVED          | Admin Override (AC-09)                   |
| SETTLED       | REOPENED          | Formal Dispute & Sub-Claim Spawn (AC-08) |
+---------------+-------------------+------------------------------------------+
```

---

## 3. Validation Logic

```
function transitionTo(claim, target_state, actor_role):
    if not isTransitionAllowed(claim.current_state, target_state):
        throw new InvalidClaimStateException(
            claim.id,
            claim.current_state,
            target_state,
            getAllowedTargets(claim.current_state)
        )
    
    // Append to transition ledger (NFR-02)
    recordStateTransition(claim.id, claim.current_state, target_state, actor_role)
    claim.current_state = target_state
```

---

## 4. Verification Checklist
- Assert all 28 illegal transitions throw `InvalidClaimStateException`.
- Assert `InvalidClaimStateException` maps to HTTP 409 Conflict.
- Assert every successful transition records an append-only audit event.
