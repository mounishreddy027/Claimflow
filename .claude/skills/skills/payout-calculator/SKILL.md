---
name: payout-calculator
description: Calculates financial claim assessments using fixed-point math and enforces the non-negative payable invariant (AC-05, NFR-01).
---

# Payout Calculator Skill

This skill provides step-by-step guidance for calculating assessment amounts, applying deductibles and co-payments, and guaranteeing the non-negative payable invariant in compliance with **AC-05** and **NFR-01**.

---

## 1. When to Use This Skill
- Implementing or refactoring `AssessmentCalculator` or financial domain value objects.
- Verifying boundary test cases where deductions exceed claim amounts.
- Validating that no floating-point arithmetic occurs in currency paths.

---

## 2. Calculation Procedure

Given inputs:
- `claim_amount` (FixedPointMoney)
- `sum_insured` (FixedPointMoney)
- `deductibles` (FixedPointMoney)
- `co_pay` (FixedPointMoney)

### Execution Steps:
1. **Step 1: Cap at Policy Limit**
   $$\text{effective\_claim} = \min(\text{claim\_amount}, \text{sum\_insured})$$
2. **Step 2: Aggregate Deductions**
   $$\text{gross\_deductions} = \text{deductibles} + \text{co\_pay}$$
3. **Step 3: Calculate Net Payable**
   $$\text{net\_payable} = \text{effective\_claim} - \text{gross\_deductions}$$
4. **Step 4: Enforce Invariant Invariance**
   $$\text{payable\_amount} = \max(0.00, \text{net\_payable})$$

---

## 3. Mandatory Invariant & Precision Guardrails

- **Zero Floating-Point Types:** Never use `float` or `double`. Use `BigDecimal` with scale 2.
- **Banker's Rounding:** Apply `RoundingMode.HALF_EVEN` on any division or fractional multiplication.
- **Zero-Clamping Test:** Always verify that when `gross_deductions > effective_claim`, the result is `$0.00` and NEVER a negative figure.
