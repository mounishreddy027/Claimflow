---
name: audit-trace
description: Audits database access, log output, and administrative actions to enforce immutability (NFR-02), PII redaction (NFR-03), and RBAC boundaries (NFR-04).
---

# /audit-trace — Audit & Compliance Verification Command

When this command is invoked, the agent performs a deep static and integration audit for regulatory compliance.

## Execution Steps

1. **Verify Immutability of Records (NFR-02):**
   - Check all queries against `claims`, `assessments`, `fraud_evaluations`, and `payout_records`.
   - Confirm zero occurrences of `UPDATE` or `DELETE` statements on historical financial records.

2. **PII Masking Audit (NFR-03):**
   - Scan application log files and filter configs for unmasked claimant identifiers (SSN, medical diagnosis narratives, bank account numbers).
   - Assert `PiiRedactionFilter` is active and passing all tests.

3. **RBAC & Controller Boundary Audit (NFR-04):**
   - Verify that `/api/v1/admin/**` endpoints are protected by `ROLE_ADMIN`.
   - Assert integration tests verify HTTP 403 Forbidden when invoked with `ROLE_ASSESSOR` or anonymous tokens.

4. **Structured Logging & Correlation IDs (NFR-06):**
   - Verify every log format includes `correlation_id` and timestamp.
