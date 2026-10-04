---
name: fraud-rule-evaluator
description: Evaluates insurance claims against deterministic fraud rules and active policy thresholds to enforce AC-04.
---

# Fraud Rule Evaluator Skill

This skill provides step-by-step guidance for calculating deterministic fraud risk scores and policy threshold evaluation in compliance with **AC-04**.

---

## 1. When to Use This Skill
- Implementing or testing the `DeterministicFraudScreeningService`.
- Verifying deterministic rule weights and boundary thresholds.
- Validating that fraud evaluations are append-only.

---

## 2. Rule Evaluation Algorithm

Execute the following 6 deterministic rule evaluations on every claim:

1. **FR-01: Rapid Inception Loss (+25 pts)**
   - Check: `daysBetween(policy.startDate, claim.incidentDate) <= 14`
   - Trigger Code: `FRAUD_RAPID_INCEPTION`
2. **FR-02: High Sum Insured Ratio (+20 pts)**
   - Check: `claim.claimAmount > (policy.sumInsured * 0.90)`
   - Trigger Code: `FRAUD_HIGH_SUM_RATIO`
3. **FR-03: Repeat Claimant Frequency (+20 pts)**
   - Check: `countClaimsByPolicy(claim.policyNumber, last12Months) >= 2`
   - Trigger Code: `FRAUD_REPEAT_CLAIMANT`
4. **FR-04: Off-Hours Incident (+15 pts)**
   - Check: `incidentTime.hour in [23, 0, 1, 2, 3, 4]`
   - Trigger Code: `FRAUD_OFF_HOURS_INCIDENT`
5. **FR-05: Round Number Amount (+10 pts)**
   - Check: `claim.claimAmount % 1000 == 0`
   - Trigger Code: `FRAUD_ROUND_AMOUNT`
6. **FR-06: Delayed Reporting (+10 pts)**
   - Check: `daysBetween(claim.incidentDate, claim.filedDate) > 30`
   - Trigger Code: `FRAUD_DELAYED_REPORTING`

### Score Aggregation:
$$\text{raw\_score} = \sum \text{triggered\_weights}$$
$$\text{fraud\_score} = \min(100, \text{raw\_score})$$

---

## 3. Threshold Comparison & Flagging

```
if fraud_score > policy.fraud_threshold:
    is_flagged = true
    decision_routing = MANUAL_REVIEW
else:
    is_flagged = false
    decision_routing = ELIGIBLE_FOR_AUTO_APPROVE
```

> **Crucial Rule:** If `fraud_score == policy.fraud_threshold`, `is_flagged` is `false`. Flagging occurs strictly when the score **strictly exceeds** the threshold.
