# Feature Specification: Financial Assessment & Deductible Engine
## Feature ID: SPEC-04 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Feature Description & Scope

The **Financial Assessment & Deductible Engine** calculates the exact payable financial settlement for a claim under adjudication. It evaluates the raw claimed damages against policy coverage limits, applies applicable policy deductibles and co-payment percentages, and produces a mathematically invariant payable amount.

This engine is governed by strict financial accuracy requirements (**NFR-01**): all calculations must execute in fixed-point decimal arithmetic, and the calculated payable amount must strictly satisfy the non-negative invariant $\text{payable\_amount} \ge 0$ under all input conditions.

---

## 2. Acceptance Criteria

### AC-05: Assessment Calculation Math & Non-Negative Invariant
**Criterion Statement:** Assessment computes `payable_amount = min(claim_amount, sum_insured) - deductibles - co_pay`; invariant `payable_amount >= 0` holds.

- **Scenario 5.1: Standard Assessment with Valid Deductions**
  - **Given** a claim with `claim_amount = $4,000.00`,
  - **And** linked policy has `sum_insured = $10,000.00`, standard `deductible = $500.00`, and `co_pay = $200.00`,
  - **When** the assessment calculation executes,
  - **Then** `effective_claim = min(4000.00, 10000.00) = $4,000.00`,
  - **And** `gross_deductions = 500.00 + 200.00 = $700.00`,
  - **And** `payable_amount = 4000.00 - 700.00 = $3,300.00`,
  - **And** invariant $\text{payable\_amount} \ge 0$ is satisfied.

- **Scenario 5.2: Claim Exceeds Policy Sum Insured (Coverage Cap)**
  - **Given** a catastrophic loss claim with `claim_amount = $25,000.00`,
  - **And** policy maximum `sum_insured = $15,000.00`, with `deductible = $1,000.00` and `co_pay = $0.00`,
  - **When** the assessment calculation executes,
  - **Then** the effective claim is capped at `sum_insured` (`$15,000.00`),
  - **And** `payable_amount = 15000.00 - 1000.00 = $14,000.00`.

- **Scenario 5.3: Deductions Exceed Claim Amount (Zero Clamping Invariant)**
  - **Given** a minor damage claim with `claim_amount = $400.00`,
  - **And** policy has `sum_insured = $5,000.00`, standard `deductible = $500.00`, and `co_pay = $100.00` (Total deductions = `$600.00`),
  - **When** the assessment calculation executes,
  - **Then** raw difference is `$400.00 - $600.00 = -$200.00`,
  - **And** the engine clamps the outcome to `payable_amount = $0.00`,
  - **And** the invariant $\text{payable\_amount} \ge 0$ is maintained without exception or negative leakage.

- **Scenario 5.4: Percentage-Based Co-Pay Evaluation**
  - **Given** a Health claim with `claim_amount = $10,000.00`, `sum_insured = $20,000.00`, zero deductible, and a 10% co-payment rule,
  - **When** the assessment is computed,
  - **Then** `co_pay = $10,000.00 * 0.10 = $1,000.00`,
  - **And** `payable_amount = $9,000.00`.

---

## 3. Mathematical Formulation & Precision Rules (NFR-01)

### Mathematical Definition:
$$\text{effective\_claim} = \min(\text{claim\_amount}, \text{sum\_insured})$$
$$\text{gross\_deductions} = \text{deductibles} + \text{co\_pay}$$
$$\text{net\_payable} = \text{effective\_claim} - \text{gross\_deductions}$$
$$\text{payable\_amount} = \max(0.00, \text{net\_payable})$$

### Fixed-Point Precision Rules:
1. **Data Type:** `java.math.BigDecimal` (Java), `decimal.Decimal` (Python), or scaled integer cents (TypeScript).
2. **Scale & Rounding:** Scale fixed to `2` decimal places. Intermediate multiplication (e.g., percentage co-pay) must apply `RoundingMode.HALF_EVEN` (Banker's rounding).
3. **No Floats:** Automated architecture test blocks `Float`, `Double`, `float`, `double` anywhere in `src/domain/`.

---

## 4. API Contract & Data Model

### 4.1 Endpoint: `POST /api/v1/claims/{claimId}/assess`
- **Authorized Role:** `ROLE_ASSESSOR` or `ROLE_ADMIN`
- **Request Body (Optional manual overrides by assessor):**
```json
{
  "additionalDeductible": 0.00,
  "assessorNotes": "Standard repair assessment confirmed against garage invoice."
}
```

- **Response Body (`200 OK`):**
```json
{
  "assessmentId": "ASM-88021",
  "claimId": "CLM-2026-00491",
  "claimAmount": 4000.00,
  "sumInsured": 10000.00,
  "effectiveClaim": 4000.00,
  "deductibleApplied": 500.00,
  "copayApplied": 200.00,
  "grossDeductions": 700.00,
  "payableAmount": 3300.00,
  "assessedAt": "2026-10-04T12:15:00Z",
  "assessedBy": "assessor_user_1"
}
```

---

## 5. Non-Functional Criteria & Guardrails

- **NFR-01:** Absolute adherence to fixed-point decimal arithmetic.
- **NFR-02:** Assessment outputs are saved to append-only `assessments` table. If re-assessed, a new record with an incremented version is created.
- **NFR-08:** Invariant test suite asserts that `payableAmount >= 0.00` across 1,000 randomized property-based test cases.
