---
name: assess-claim
description: Interactively runs financial assessment calculations for a claim, validating payable math, deductibles, co-pay, and the non-negative payable invariant.
---

# /assess-claim — Claim Financial Assessment Command

When this command is invoked, the agent simulates or executes an assessment calculation according to **AC-05** and **NFR-01**.

## Execution Steps

1. **Prompt for Claim & Policy Inputs (or accept claim ID):**
   - `claim_amount` (e.g., $4,000.00)
   - `sum_insured` (e.g., $10,000.00)
   - `deductible` (e.g., $500.00)
   - `co_pay` (e.g., $200.00 or percentage)

2. **Execute Fixed-Point Calculation:**
   $$\text{effective\_claim} = \min(\text{claim\_amount}, \text{sum\_insured})$$
   $$\text{gross\_deductions} = \text{deductibles} + \text{co\_pay}$$
   $$\text{net\_payable} = \text{effective\_claim} - \text{gross\_deductions}$$
   $$\text{payable\_amount} = \max(0.00, \text{net\_payable})$$

3. **Verify Invariants:**
   - Confirm `payable_amount >= 0.00` strictly holds.
   - Confirm all amounts are represented as 2-decimal fixed-point numbers with Banker's rounding (`HALF_EVEN`).
   - Print a breakdown report of effective coverage and deductions.
