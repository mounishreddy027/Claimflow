# Feature Specification: Adjudication Decisioning & Settlement Payout
## Feature ID: SPEC-05 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Feature Description & Scope

The **Adjudication Decisioning & Settlement Payout** module governs the final resolution of assessed claims and the execution of financial settlements.

Based on document verification, deterministic fraud screening results, policy coverage checks, and calculated assessments, the module issues an adjudication decision (`AUTO_APPROVE`, `MANUAL_REVIEW`, or `REJECT`) accompanied by standard reason codes referenced directly from the versioned insurance policy. 

When a claim is approved, the settlement engine generates an **immutable payout record** linked to the claim, ensuring that `payout_amount` strictly equals the assessed `payable_amount`, transitions the claim to `SETTLED`, and triggers a stubbed disbursement transaction.

---

## 2. Acceptance Criteria

### AC-06: Adjudication Decision & Policy Reason Codes
**Criterion Statement:** Decision returns `AUTO_APPROVE` / `MANUAL_REVIEW` / `REJECT` with reason codes referenced from the versioned policy.

- **Scenario 6.1: Straight-Through Automated Approval (`AUTO_APPROVE`)**
  - **Given** a claim in `UNDER_REVIEW` status with all documents `VERIFIED`,
  - **And** deterministic `fraudScore` is below the policy threshold (`isFlagged = false`),
  - **And** assessed `payable_amount > $0.00`,
  - **When** the decision engine evaluates the claim,
  - **Then** the decision returned is `AUTO_APPROVE`,
  - **And** reason code is set to `"POL_APPR_STP_01"` (*Standard Straight-Through Processing Approval*),
  - **And** the claim state advances to `APPROVED`.

- **Scenario 6.2: Fraud Flag Diverts to Manual Review (`MANUAL_REVIEW`)**
  - **Given** a claim where deterministic fraud score exceeded threshold (`isFlagged = true`),
  - **When** the decision engine runs,
  - **Then** the decision returned is `MANUAL_REVIEW`,
  - **And** reason code references `"POL_REV_FRAUD_FLAG_02"`,
  - **And** the claim remains in `UNDER_REVIEW` awaiting assessor sign-off.

- **Scenario 6.3: Claim Rejection with Policy Reason Code (`REJECT`)**
  - **Given** an assessed claim with policy exclusion or non-covered peril,
  - **When** the assessor or engine issues a rejection,
  - **Then** the decision returned is `REJECT`,
  - **And** reason code references an explicit policy clause (e.g., `"POL_REJ_EXCLUSION_03"` or `"POL_REJ_INSUFFICIENT_DOCS_04"`),
  - **And** the claim transitions directly from `UNDER_REVIEW` to `REJECTED`.

---

### AC-07: Immutable Settlement Payout Generation
**Criterion Statement:** Settlement generates an immutable payout record linked to the claim; `payout_amount` equals the assessed amount.

- **Scenario 7.1: Immutable Payout Creation on Approval**
  - **Given** a claim with assessed `payable_amount = $3,300.00` transitioning to `APPROVED`,
  - **When** settlement processing is initiated,
  - **Then** the system creates a new record in `payout_records`,
  - **And** `payout_amount` is set strictly to `$3,300.00` (exact equality to assessed amount),
  - **And** the payout record is linked to `claimId`,
  - **And** the payout record is marked with status `DISBURSED` (via stubbed disbursement rail),
  - **And** the claim state transitions from `APPROVED` to `SETTLED`.

- **Scenario 7.2: Invariant Check on Payout Amount Mismatch**
  - **Given** an attempt to create a payout record where requested payout differs from the assessed `payable_amount` (e.g., assessed $3,300.00 vs requested $3,500.00),
  - **When** the settlement service processes the record,
  - **Then** the operation is aborted with `PayoutInvariantViolationException`,
  - **And** no payout record is persisted, and the state transition to `SETTLED` is blocked.

- **Scenario 7.3: Append-Only Payout Immutability (NFR-02)**
  - **Given** an existing payout record in `payout_records`,
  - **When** an application code path or database statement attempts to `UPDATE` or `DELETE` the record,
  - **Then** database constraints and repository guards abort the transaction,
  - **And** the historical payout amount remains permanently unmodified.

---

## 3. Standard Policy Reason Codes Catalog

| Reason Code | Decision Category | Policy Clause Description |
|---|---|---|
| `POL_APPR_STP_01` | `AUTO_APPROVE` | Straight-Through Processing: Full document compliance, zero fraud flags. |
| `POL_APPR_MANUAL_02`| `AUTO_APPROVE` / Assessor | Assessor verified and approved following manual risk assessment. |
| `POL_REV_FRAUD_FLAG_01`| `MANUAL_REVIEW` | Deterministic fraud risk score exceeded policy threshold. |
| `POL_REV_DOC_ANOMALY_02`| `MANUAL_REVIEW` | Discrepancy observed between claimed amounts and repair invoice. |
| `POL_REJ_EXCLUSION_01`| `REJECT` | Event explicitly excluded under Policy Schedule Section 4 (General Exclusions). |
| `POL_REJ_INSUFFICIENT_DOCS_02`| `REJECT` | Claimant failed to furnish mandatory certified documentation within 60 days. |
| `POL_REJ_ZERO_PAYABLE_03`| `REJECT` | Assessed payable amount after deductibles is $0.00. |

---

## 4. API Contract & Data Model

### 4.1 Endpoint: `POST /api/v1/claims/{claimId}/settle`
- **Authorized Role:** `ROLE_ASSESSOR` or System Workflow
- **Response Body (`200 OK`):**
```json
{
  "payoutId": "PAY-2026-99120",
  "claimId": "CLM-2026-00491",
  "payoutAmount": 3300.00,
  "currency": "USD",
  "status": "DISBURSED",
  "disbursementRail": "STUBBED_ACH",
  "recipientMaskedAccount": "XXXX-XXXX-1926",
  "settledAt": "2026-10-04T12:20:00Z"
}
```

---

## 5. Non-Functional Criteria & Guardrails

- **NFR-01:** `payout_amount` evaluated using fixed-point `BigDecimal` (scale 2).
- **NFR-02:** Table `payout_records` is append-only with no update/delete triggers.
- **NFR-08:** Automated test verifies `assert(payout.amount.equals(assessment.payableAmount))`.
