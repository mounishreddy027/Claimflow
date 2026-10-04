---
name: audit-tracer
description: Verifies append-only storage guarantees (NFR-02), PII redaction in logs (NFR-03), and role separation boundaries (NFR-04).
---

# Audit Tracer Skill

This skill provides procedures for auditing data immutability, log privacy, and role-based controller security across ClaimFlow.

---

## 1. When to Use This Skill
- Auditing repository implementations for forbidden `UPDATE` or `DELETE` SQL queries.
- Inspecting logger interceptors for PII leakage.
- Validating controller role boundaries and administrative overrides.

---

## 2. Immutability Verification (NFR-02)

Audit the following entity repositories:
- `ClaimRepository`: State transitions must insert into `claim_state_transitions`.
- `FraudReportRepository`: Scores are inserted once, never modified.
- `AssessmentRepository`: Assessments are versioned inserts.
- `PayoutLedgerRepository`: Payout records cannot be altered.

### Disallowed Patterns:
- `UPDATE payout_records SET ...` -> **FORBIDDEN**
- `DELETE FROM claims WHERE ...` -> **FORBIDDEN**
- Direct in-memory setter mutation on finalized entities -> **FORBIDDEN**

---

## 3. PII Redaction Verification (NFR-03)

Ensure that all logging configurations include masking filters for:
- Social Security Numbers / National IDs: `\b\d{3}-\d{2}-\d{4}\b` -> `[REDACTED_SSN]`
- Bank Account Numbers / IBANs: `\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b` -> `[REDACTED_IBAN]`
- Medical Diagnoses & Symptoms: Field-level redaction on health narratives.
- Full Names & Physical Addresses.

---

## 4. Administrative Override Audit (AC-09)

Every override must persist:
1. `claimId`
2. `actorId` (authenticated admin username)
3. `previousDecision`
4. `newDecision`
5. `reasonCode` (valid policy reason string)
6. `comment` (non-empty justification)
7. `timestamp` (UTC ISO-8601)
