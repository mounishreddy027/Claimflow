# src/repositories/CLAUDE.md — Persistence & Ledger Repository Guidelines

This document governs the database persistence and repository implementation layer (`src/repositories/`).

---

## 1. Immutability & Append-Only Guarantees (NFR-02)

To satisfy regulatory insurance auditing standards:
1. **Append-Only Ledgers:**
   - `claim_state_transitions`: Append new state transition row.
   - `fraud_evaluations`: Append-only scores and triggered rules.
   - `assessments`: Append-only assessment versions.
   - `payout_records`: Immutable payout transactions.
   - `claim_override_audits`: Immutable audit trail for admin actions.
2. **Forbidden SQL Statements:**
   - Direct `UPDATE` or `DELETE` on financial ledgers is strictly barred.
   - Any archival or reversal must be accomplished by appending a new compensating record.

---

## 2. Migration Guidelines (NFR-05)

- All schema migration scripts (`V1__...`, `V2__...`) must be **strictly forward-only and append-only**.
- `DROP TABLE`, `DROP COLUMN`, or `TRUNCATE` operations are strictly forbidden.
- Columns must be added with non-null defaults or nullable flags to preserve backward compatibility.

---

## 3. Query Separation & Performance

- **Fast Historical Queries:** Repositories must support efficient retrieval of claim history, sub-claims, and audit logs by `claimId`.
- **Indexing:** Primary keys (`UUID`), foreign keys (`claim_id`, `policy_number`), and status fields must be indexed to ensure fast query latency.
