# Knowledge Deposits & Learned Engineering Rules
## Document Version: 1.0.0 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Overview & Purpose

In long-running autonomous development with Claude Code agents, recurring mistakes and subtle domain regressions must not be solved ad-hoc. Under the **Karpathy Ratchet** framework, every resolved failure or discovered pitfall is codified into a permanent **Knowledge Deposit**. 

These deposits are formally integrated back into:
1. Architectural linters and automated tests (`tests/architecture/`)
2. Verification skills (`.claude/skills/`)
3. Substrate hook rules (`.claude/hooks/`)
4. Layered prompt instructions (`src/**/CLAUDE.md`)

---

## 2. Codified Knowledge Deposits

### Deposit KD-001: Floating-Point Financial Drift
- **Discovered Issue:** Agent generated assessment math using primitive floating-point types (`double`/`float`), leading to IEEE-754 precision artifacts (e.g., `$4250.0000000000005` or rounding drift on partial cents).
- **Domain Impact:** Violates **NFR-01**; insurance settlements must be exact to the cent.
- **Permanent Remediation:**
  - Implemented `FixedPointMoney` Value Object wrapping `BigDecimal` with explicit scale 2 and `RoundingMode.HALF_EVEN`.
  - Added ArchTest rule `noFloatingPointInFinancialCalculations` to fail CI if `float` or `double` is used in domain/financial models.
  - Codified in skill: `.claude/skills/payout-calculator/SKILL.md`.

---

### Deposit KD-002: Negative Payable Amount on High-Deductible Claims
- **Discovered Issue:** When deductible plus co-pay exceeded the claim amount (e.g., Claim = $800, Deductible = $1000), naive subtraction produced a negative payable amount (-$200).
- **Domain Impact:** Violates the fundamental invariant of **AC-05**: $\text{payable\_amount} \ge 0$.
- **Permanent Remediation:**
  - Hardened formula: `effective_claim = min(claim, sum_insured); payable = max(0, effective_claim - deductibles - co_pay)`.
  - Created automated invariant test suite verifying zero-clamping under 15 distinct boundary conditions.
  - Codified in hook check: `payout-invariant-check.sh` specification.

---

### Deposit KD-003: Accidental Mutation of Settled Claims
- **Discovered Issue:** Reopen feature attempted to update the status column of the existing settled claim directly in SQL (`UPDATE claims SET status = 'REOPENED' WHERE id = ...`), violating append-only history.
- **Domain Impact:** Violates **NFR-02** and regulatory audit standards; historical settlement state was overwritten.
- **Permanent Remediation:**
  - Implemented append-only state transition ledger (`claim_state_transitions`). Original claim record remains immutable; a transition event is inserted.
  - Reopen generates a linked child sub-claim with a foreign key referencing the original claim ID (**AC-08**).
  - Codified in skill: `.claude/skills/audit-tracer/SKILL.md`.

---

### Deposit KD-004: Sensitive Claimant PII Leaked to Application Logs
- **Discovered Issue:** Controller loggers serialized entire `ClaimIntakeRequest` payloads containing claimant name, SSN, medical diagnosis, and bank IBAN into standard console output.
- **Domain Impact:** Severe violation of **NFR-03** and insurance privacy laws (HIPAA/GDPR).
- **Permanent Remediation:**
  - Introduced `PiiRedactionFilter` which intercepts all JSON log payloads and masks sensitive fields using regex token replacement.
  - Added static analysis test scanning for unmasked toString() logging of claimant entities.
  - Codified in root `CLAUDE.md` and `src/controllers/CLAUDE.md`.

---

### Deposit KD-005: Out-of-Order State Transition Bypassing Review
- **Discovered Issue:** Agent wrote an automated integration test that directly transitioned a claim from `FILED` to `APPROVED`, skipping `UNDER_REVIEW` and document verification.
- **Domain Impact:** Violates **AC-10**; state machine must strictly enforce `FILED` → `UNDER_REVIEW` → `APPROVED`/`REJECTED` → `SETTLED` → `REOPENED`.
- **Permanent Remediation:**
  - Enforced transition validation inside `ClaimStateMachine.transitionTo()`. Any invalid transition immediately raises `InvalidClaimStateException`.
  - Added exhaustive permutation test suite validating all 36 combinations of state transitions (5 valid, 31 illegal).
  - Codified in skill: `.claude/skills/state-machine-validator/SKILL.md`.

---

### Deposit KD-006: Missing Reason Code on Admin Override
- **Discovered Issue:** Admin override endpoint allowed changing an adjudication decision from `REJECT` to `AUTO_APPROVE` with only a freeform comment, omitting the structured policy reason code.
- **Domain Impact:** Violates **AC-09**; administrative overrides must record both a standardized reason code and an explanatory comment for regulatory compliance.
- **Permanent Remediation:**
  - Request DTO updated to require non-empty `reasonCode` and `justificationComment`.
  - Audit repository guarantees persistence of admin actor identity, timestamp, previous decision, new decision, and reason code.
  - Codified in specification: `specs/admin_override_spec.md`.

---

## 3. Knowledge Deposit Lifecycle

When any future agent observes an evaluator failure or regression:
1. Diagnose root cause using `/systematic-debugging`.
2. Implement regression test in the test suite.
3. Fix domain implementation.
4. Record finding as `KD-NNN` in this document.
5. Update corresponding skill and layered `CLAUDE.md` to prevent recurrence.
