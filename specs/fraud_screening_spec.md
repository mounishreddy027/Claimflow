# Feature Specification: Deterministic Fraud Screening Engine
## Feature ID: SPEC-03 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Feature Description & Scope

The **Deterministic Fraud Screening Engine** provides rule-based fraud risk scoring for every verified claim. To comply with strict insurance auditability, the scoring algorithm is 100% deterministic (reproducible), non-stochastic, and free of external non-deterministic machine learning dependencies.

The engine computes an aggregate fraud risk score ranging from `0` to `100`. It compares this score against the `fraudThreshold` defined in the active version of the governing insurance policy. If the computed score strictly exceeds the policy threshold, the claim is flagged with `isFlagged = true` and a collection of trigger reason codes, mandating manual adjuster review.

---

## 2. Acceptance Criteria

### AC-04: Deterministic Fraud Scoring and Threshold Flagging
**Criterion Statement:** Fraud screening returns a deterministic score; claim is flagged when score exceeds the configured threshold from the active policy version.

- **Scenario 4.1: Low-Risk Claim Scoring Below Policy Threshold**
  - **Given** an active policy `"POL-MTR-1001"` with configured `fraudThreshold = 50`,
  - **When** a claim with no triggered risk rules is evaluated,
  - **Then** the engine returns a deterministic `fraudScore = 0`,
  - **And** `isFlagged` is evaluated as `false`,
  - **And** the claim remains eligible for automated straight-through processing (`AUTO_APPROVE`).

- **Scenario 4.2: High-Risk Claim Exceeding Policy Threshold**
  - **Given** an active policy `"POL-HLT-2002"` with configured `fraudThreshold = 40`,
  - **When** a claim triggers Rule FR-01 (Rapid filing after inception: +25 pts) and Rule FR-02 (Claim amount > 90% of sum insured: +20 pts),
  - **Then** the engine computes total `fraudScore = 45`,
  - **And** since `45 > 40`, `isFlagged` evaluates to `true`,
  - **And** triggered reason codes `["FRAUD_RAPID_INCEPTION", "FRAUD_HIGH_SUM_RATIO"]` are appended,
  - **And** downstream decisioning is barred from `AUTO_APPROVE` and diverted to `MANUAL_REVIEW`.

- **Scenario 4.3: Policy Version Sensitivity**
  - **Given** Policy Version 1 with threshold `50` and Policy Version 2 with tightened threshold `35`,
  - **When** a claim with fraud score `40` is evaluated against Policy Version 1,
  - **Then** it is NOT flagged (`40 <= 50`),
  - **When** the identical claim is evaluated against Policy Version 2,
  - **Then** it IS flagged (`40 > 35`), proving deterministic threshold binding to the active policy version.

- **Scenario 4.4: Boundary Condition (Score Equals Threshold)**
  - **Given** a policy with `fraudThreshold = 50`,
  - **When** a claim scores exactly `50`,
  - **Then** `isFlagged` is `false` (flagging occurs strictly when `score > threshold`).

---

## 3. Deterministic Fraud Rules Catalog

| Rule ID | Rule Name | Condition & Criteria | Score Weight | Trigger Code |
|---|---|---|---|---|
| **FR-01** | Rapid Inception Loss | Incident occurred within 14 calendar days of policy start date | **+25** | `FRAUD_RAPID_INCEPTION` |
| **FR-02** | Near-Ceiling Claim Amount | `claimAmount` exceeds 90% of policy `sumInsured` | **+20** | `FRAUD_HIGH_SUM_RATIO` |
| **FR-03** | High Claim Frequency | Policy has had ≥ 2 claims filed within preceding 12 months | **+20** | `FRAUD_REPEAT_CLAIMANT` |
| **FR-04** | Off-Hours / Weekend Incident | Incident timestamp recorded between 23:00 and 04:00 local time | **+15** | `FRAUD_OFF_HOURS_INCIDENT` |
| **FR-05** | Round Number Claim Amount | Claim amount is an exact multiple of 1,000 (e.g., $5,000.00) without itemized cents | **+10** | `FRAUD_ROUND_AMOUNT` |
| **FR-06** | Incomplete Doc Submission Delay | More than 30 days elapsed between incident date and initial filing | **+10** | `FRAUD_DELAYED_REPORTING` |

*Maximum Possible Score:* Clamped to `100`.

---

## 4. API Contract & Persistence Specification

### 4.1 Internal Engine Signature / DTO
```json
{
  "claimId": "CLM-2026-00491",
  "policyVersion": 1,
  "evaluatedAt": "2026-10-04T12:10:00Z",
  "fraudScore": 45,
  "policyThreshold": 40,
  "isFlagged": true,
  "triggeredRules": [
    { "ruleId": "FR-01", "weight": 25, "reasonCode": "FRAUD_RAPID_INCEPTION" },
    { "ruleId": "FR-02", "weight": 20, "reasonCode": "FRAUD_HIGH_SUM_RATIO" }
  ]
}
```

---

## 5. Non-Functional Criteria & Guardrails

- **NFR-01:** Integer calculations for scores [0–100]; percentage comparisons using fixed-point `BigDecimal`.
- **NFR-02:** All fraud evaluation reports are stored in an append-only ledger (`fraud_evaluations`). Reports cannot be edited or deleted.
- **NFR-06:** Evaluator logs include `correlation_id`, `claim_id`, `fraud_score`, and `is_flagged` (excluding claimant PII).
