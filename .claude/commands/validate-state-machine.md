---
name: validate-state-machine
description: Runs exhaustive validation across all 36 state transitions in the Claim Lifecycle State Machine to enforce AC-10.
---

# /validate-state-machine — Claim State Machine Validation Command

When this command is invoked, the agent executes comprehensive permutation testing against `ClaimStateMachine`.

## Execution Steps

1. **Verify Valid State Paths:**
   - `NONE` → `FILED`
   - `FILED` → `UNDER_REVIEW`
   - `UNDER_REVIEW` → `APPROVED`
   - `UNDER_REVIEW` → `REJECTED`
   - `APPROVED` → `SETTLED`
   - `APPROVED` → `REJECTED` (Admin Override)
   - `REJECTED` → `APPROVED` (Admin Override)
   - `SETTLED` → `REOPENED`
   Assert all 8 valid transitions succeed without exception.

2. **Verify Forbidden Transitions (28 Illegal Combinations):**
   - Attempt skipping: `FILED` → `APPROVED` (Must throw `InvalidClaimStateException`).
   - Attempt illegal regressions: `SETTLED` → `UNDER_REVIEW` (Must throw `InvalidClaimStateException`).
   - Attempt illegal jump from terminal: `REJECTED` → `SETTLED` (Must throw `InvalidClaimStateException`).
   - Assert all 28 illegal transitions raise `InvalidClaimStateException`.

3. **Verify Transition Ledger:**
   - Confirm every valid transition writes an append-only event to `claim_state_transitions`.
