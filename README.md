# ClaimFlow — Autonomous Insurance Claims Lifecycle Platform

> **Business Context:** BC-AINE-005 | **Sprint Contract:** SC-2026-01 | **Architecture:** Layered DDD & WORM Ledger

ClaimFlow is a production-grade insurance claims orchestration engine built with strict domain-driven design, deterministic fraud detection, fixed-point financial calculation, and an append-only cryptographically-chained audit trail.

---

## 1. System Architecture & Layered Boundaries

ClaimFlow strictly enforces clean architectural separation (verified by automated structural architecture tests per **NFR-08**):

```
┌────────────────────────────────────────────────────────┐
│               API Controllers / Routes                 │
│  (claims, documents, assessment, settlement, admin)    │
└───────────────────────────┬────────────────────────────┘
                            │ depends on
┌───────────────────────────▼────────────────────────────┐
│                    Domain Services                     │
│  (assessment_engine, fraud_service, settlement, audit) │
└───────────────────────────┬────────────────────────────┘
                            │ depends on
┌───────────────────────────▼────────────────────────────┐
│               Repositories & Adapters                  │
│  (claim_repo, audit_repo, settlement_repo, doc_repo)   │
└───────────────────────────┬────────────────────────────┘
                            │ depends on
┌───────────────────────────▼────────────────────────────┐
│                     Domain Core                        │
│   (Claim, ClaimStateMachine, StateTransitionRecord)    │
└───────────────────────────┬────────────────────────────┘
                            │ depends on
┌───────────────────────────▼────────────────────────────┐
│                    Types & Enums                       │
│    (ClaimState, ActorRole, AuditLogEntry, Exceptions)  │
└────────────────────────────────────────────────────────┘
```

- **Domain Core Isolation:** The `domain` layer has zero imports of database adapters, web frameworks, or controllers.
- **Immutability First:** Critical accounting records (`AuditLogEntry`, `PayoutRecord`, `StateTransitionRecord`, `Assessment`, `SubClaim`) are frozen dataclasses (`frozen=True`) preventing runtime mutation (**NFR-02**).
- **Zero `Any` Typing:** Complete type safety strictly enforced via `mypy --strict` with zero typing escapes.

---

## 2. Core Domain Subsystems

### 2.1 First Notice of Loss (FNOL) & Policy Temporal Validation (AC-01, AC-02)
- Claim submission via `POST /api/v1/claims/intake`.
- Validates policy status against incident date:
  - If incident date falls outside `[effective_date, expiry_date]`, rejects with `PolicyNotActiveException` (`HTTP 422`).
  - Validates policy status (`ACTIVE`, `LAPSED`, `EXPIRED`, `CANCELLED`).
  - Pre-populates document checklist requirements upon claim creation.

### 2.2 Document Checklist Engine (AC-03)
- Line-of-business (LOB) specific document checklists:
  - **MOTOR:** Police FIR (`POLICE_FIR`), Repair Estimate / Final Invoice (`REPAIR_INVOICE`).
  - **HEALTH:** Hospital Bill (`HOSPITAL_BILL`), Discharge Summary (`DISCHARGE_SUMMARY`).
  - **LIFE:** Death Certificate (`DEATH_CERTIFICATE`), Autopsy Report (`AUTOPSY_REPORT`).
- Enforces verification transition: Claim state remains `FILED` until all mandatory documents are marked `VERIFIED`, advancing state automatically to `UNDER_REVIEW`.

### 2.3 Deterministic Fraud Screening Engine (AC-04)
- 6 deterministic rule evaluators:
  - `FR-01`: Rapid claim submission within 48 hours of policy issuance (+25 pts).
  - `FR-02`: High claim amount exceeding 80% of total sum insured (+20 pts).
  - `FR-03`: Weekend / late-night incident timing (+10 pts).
  - `FR-04`: Missing official police report for high-value claims > $2,000 (+30 pts).
  - `FR-05`: Suspicious keywords in incident description (+15 pts).
  - `FR-06`: Rapid repeat claims on same policy (+25 pts).
- Outputs deterministic fraud score in range `[0, 100]`. If score exceeds policy threshold (default 40), the claim is flagged with `fraud_detected = True`.

### 2.4 Financial Assessment Engine (AC-05, NFR-01)
- Uses Python `Decimal` fixed-point arithmetic with Banker's rounding (`ROUND_HALF_EVEN`). Floating-point arithmetic is strictly banned.
- Core assessment formula:
  $$\text{effective\_loss} = \min(\text{claim\_amount}, \text{sum\_insured})$$
  $$\text{net\_assessment} = \text{effective\_loss} - \text{deductible} - \text{copay}$$
  $$\text{payable\_amount} = \max(0.00, \text{net\_assessment})$$
- Non-negative invariant strictly verified ($\text{payable\_amount} \ge 0.00$).

### 2.5 Settlement Engine & WORM Payout Ledger (AC-06, AC-07, NFR-02)
- Automated adjudication decision tree:
  - `AUTO_APPROVE`: Fraud score < 25, claim $\le \$2,500$, complete documents.
  - `MANUAL_REVIEW`: Fraud score in $[25, 40]$ or claim $> \$2,500$.
  - `REJECT`: Policy inactive, fraud score $> 40$, or duplicate submission.
- Write-Once-Read-Many (WORM) payout ledger:
  - Payout disbursement verifies $\text{payout\_amount} == \text{assessed\_payable\_amount}$.
  - Any attempt to update, alter, or delete an existing payout raises `ImmutabilityViolationError`.

### 2.6 Sub-Claim & Dispute Workflow (AC-08)
- Allows customers to reopen settled claims with dispute categories (`SUPPLEMENTAL_DAMAGE`, `UNRESOLVED_LIABILITY`).
- Original parent claim transitions from `SETTLED` to `REOPENED`, and a linked child `SubClaim` is spawned in `UNDER_REVIEW` state, preserving end-to-end historical lineage.

### 2.7 Administrative Override & RBAC (AC-09, NFR-04)
- Segregation of duties: Only `ROLE_ADMIN` can override assessor decisions via `POST /api/v1/admin/claims/{claim_id}/override`.
- Non-admin actors attempting overrides receive `HTTP 403 Forbidden`.
- Every override requires a versioned reason code, mandatory comments, and writes an un-tamperable audit record.

### 2.8 Claim Lifecycle State Machine (AC-10)
- Enforces canonical transition graph:
  $$\text{None} \to \text{FILED} \to \text{UNDER\_REVIEW} \to \begin{cases} \text{APPROVED} \to \text{SETTLED} \to \text{REOPENED} \\ \text{REJECTED} \end{cases}$$
- Rejection of illegal transitions with `InvalidClaimStateException`.
- Validated via exhaustive $6 \times 6$ transition matrix unit test (exactly 7 valid transitions, 29 rejected transitions).

### 2.9 Immutable Audit Trail & Hash-Chained WORM Ledger (AC-09, NFR-02, NFR-03)
- Cryptographic hash chaining: Each entry includes SHA-256 digest computed as:
  $$\text{hash}_n = \text{SHA256}(\text{hash}_{n-1} + \text{log\_id} + \text{claim\_id} + \text{operation\_type} + \text{canonical\_payload})$$
- PII Sanitization: Recursive regex filter automatically replaces SSN, credit card, bank account, and sensitive medical data with `[REDACTED]` prior to hash calculation and persistence.

---

## 3. Sprint 1 Contract Verification Matrix

All 6 Evaluator Quality Gates defined in `sprint-contracts/sprint-01-contract.md` have been fulfilled and verified:

| Quality Gate | Requirement | Status | Evidence |
|---|---|:---:|---|
| **Gate 1: Service Health** | Application boots cleanly; `GET /health` returns HTTP 200 with latency < 1,000ms (**NFR-07**) | **PASS** | `GET /health` responds in < 10ms with `{"status":"ok"}`. |
| **Gate 2: AC Verification** | 100% of scenarios in intake, doc verification, and state machine specs pass; tests tagged with AC markers | **PASS** | 75/75 tests pass across unit and integration suites tagged with `@pytest.mark.AC_*`. |
| **Gate 3: Coverage Ratchet** | Code coverage in `src/domain/` reaches $\ge 85\%$ (hard floor 80%) | **PASS** | `src/domain/` achieved **100%** coverage; overall backend coverage is **93%**. |
| **Gate 4: Architecture Integrity** | Zero architecture violations; domain isolated from external layers (**NFR-08**) | **PASS** | Automated AST tests verify layer separation and frozen dataclasses. |
| **Gate 5: Append-Only Compliance** | State machine transition history and payout records verified append-only (**NFR-02**) | **PASS** | `ImmutabilityViolationError` raised on update/delete; hash chain integrity verified. |
| **Gate 6: Security & PII** | Zero claimant PII written to log outputs (**NFR-03**) | **PASS** | Automated sanitization tests verify SSN, credit cards, and bank details masked as `[REDACTED]`. |

---

## 4. Test Execution & Coverage Report

### Summary
- **Total Tests:** 75
- **Passed:** 75 (100%)
- **Failed:** 0
- **Flaky / Skipped:** 0
- **Overall Code Coverage:** 93%
- **Domain Layer Coverage:** 100%
- **Static Type Checking:** Clean (`mypy` across 59 source files, 0 errors)
- **Linting & Code Style:** Clean (`ruff`, 0 errors)

### Coverage by Module

| Module | Statements | Missing | Coverage |
|---|---|---|---|
| `claimflow/domain/claim.py` | 17 | 0 | **100%** |
| `claimflow/domain/state_machine.py` | 27 | 0 | **100%** |
| `claimflow/services/assessment_engine.py` | 17 | 0 | **100%** |
| `claimflow/services/fraud_service.py` | 43 | 0 | **100%** |
| `claimflow/services/policy_service.py` | 15 | 0 | **100%** |
| `claimflow/services/audit_service.py` | 29 | 0 | **100%** |
| `claimflow/services/settlement_service.py` | 42 | 2 | **95%** |
| `claimflow/repositories/claim_repository.py` | 43 | 2 | **95%** |
| `claimflow/repositories/document_repository.py` | 41 | 4 | **90%** |
| `claimflow/repositories/audit_repository.py` | 63 | 7 | **89%** |
| `claimflow/repositories/settlement_repository.py` | 30 | 5 | **83%** |
| `claimflow/repositories/policy_repository.py` | 11 | 2 | **82%** |
| `claimflow/api/routes/claims.py` | 42 | 1 | **98%** |
| `claimflow/api/routes/assessment.py` | 29 | 2 | **93%** |
| `claimflow/api/routes/settlement.py` | 29 | 5 | **83%** |
| `claimflow/api/routes/documents.py` | 34 | 4 | **88%** |
| `claimflow/api/routes/disputes.py` | 25 | 4 | **84%** |
| `claimflow/api/routes/overrides.py` | 31 | 7 | **77%** |
| `claimflow/api/routes/audit.py` | 10 | 0 | **100%** |
| `claimflow/utils/financial.py` | 16 | 0 | **100%** |
| `claimflow/utils/pii_redaction.py` | 23 | 2 | **91%** |
| **TOTAL** | **993** | **65** | **93%** |

---

## 5. Getting Started & Running the Application

### 5.1 Prerequisites
- Python 3.10+ (tested on Python 3.14)
- `pip` or virtual environment manager

### 5.2 Installation
```bash
# Navigate to the backend directory
cd backend

# Install dependencies
pip install -e .
```

### 5.3 Running the Test Suite
```bash
# Run all unit, integration, and architecture tests
python -m pytest

# Run tests with test coverage breakdown
python -m pytest --cov=src --cov-report=term-missing

# Run only acceptance criteria tests for Sprint 1
python -m pytest -m "AC_01 or AC_02 or AC_03 or AC_10"
```

### 5.4 Running Linting & Type Checking
```bash
# Run Ruff linter
python -m ruff check src tests

# Run Mypy static type checker
python -m mypy src tests
```

### 5.5 Running the FastAPI Application
```bash
# Start the Uvicorn ASGI server
uvicorn claimflow.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Probe:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 6. API Reference Overview

| Method | Endpoint | Description | AC / NFR |
|---|---|---|---|
| `GET` | `/health` | Application liveness probe | NFR-07 |
| `POST` | `/api/v1/claims/intake` | Submit First Notice of Loss (FNOL) | AC-01, AC-02 |
| `GET` | `/api/v1/claims/{id}` | Retrieve claim details and current status | AC-01 |
| `GET` | `/api/v1/claims/{id}/documents` | Retrieve claim document checklist status | AC-03 |
| `POST` | `/api/v1/claims/{id}/documents/{doc_id}/verify` | Verify or reject document checklist item | AC-03 |
| `POST` | `/api/v1/claims/{id}/assess` | Perform financial assessment and fraud scoring | AC-04, AC-05 |
| `POST` | `/api/v1/claims/{id}/settle` | Adjudicate settlement and disburse payout | AC-06, AC-07 |
| `POST` | `/api/v1/claims/{id}/reopen` | Reopen settled claim with dispute details | AC-08 |
| `POST` | `/api/v1/admin/claims/{id}/override` | Admin override of adjudication decision | AC-09, NFR-04 |
| `GET` | `/api/v1/audit-trail/{id}` | Fetch hash-chained, PII-sanitized audit log | AC-09, NFR-02 |
