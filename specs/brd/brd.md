# Business Requirements Document — FNOL-to-Settlement Claims Pipeline

**Project:** ClaimFlow Insurance Claims Management System  
**Version:** 1.0  
**Date:** 2026-10-04  
**Prepared by:** Planner Agent (Claude Harness Engine)  
**Status:** Approved for `/spec` phase

---

## Executive Summary

ClaimFlow automates the end-to-end First Notice of Loss (FNOL) to settlement claims pipeline for Horizon Insurance, reducing processing time from 5–7 days to under 1 hour for auto-approved claims and under 24 hours for manual assessments. The system enforces deterministic fraud screening rules, eliminates calculation errors through WORM (Write-Once-Read-Many) persistence, and implements audit-trail compliance for SOX, GDPR, and 7-year regulatory retention. The MVP spans all six core stages (intake, validation, fraud check, assessment, decisioning, payout) across three development sprints, supporting motor, health, and life insurance lines of business with distinct document verification workflows.

---

## Problem Statement

### Current State
Horizon Insurance's claims operations suffer from four critical inefficiencies:

1. **Manual FNOL Intake:** Paper-heavy intake delays claim processing cycles to 5–7 days. Document verification is inconsistent across lines of business (motor, health, life), requiring manual checklist review for each claim.

2. **Weak Fraud Screening:** Lack of deterministic fraud rules allows high-risk claims to slip through to assessment, increasing operational exposure. Current screening is subjective and error-prone.

3. **Settlement Calculation Errors:** Manual settlement calculations introduce floating-point rounding errors and payable discrepancies, creating reconciliation issues and customer disputes.

4. **Audit & Compliance Gaps:** Lack of immutable claim records and override audit trails violates SOX, GDPR, and insurance regulatory standards. No way to trace who authorized changes or when.

### Impact
- Claims sit in queues 5–7 days before processing begins
- Fraudulent or high-risk claims are sometimes approved, increasing payout exposure
- Rounding errors and manual overrides create reconciliation work
- Auditors flag compliance gaps (missing audit trails, mutable records)
- Cost per claim: $45 (labor-intensive manual process)

### Success Criteria
The system must reduce processing time, improve accuracy, and lower cost while maintaining full audit compliance:
- **Processing Time:** Under 1 hour for auto-approvals; under 24 hours for manual assessments
- **Fraud Detection:** 100% deterministic rule enforcement—no claims exceed fraud thresholds without explicit override
- **Cost Reduction:** Under $10 per claim at 10k monthly volume (82% reduction)
- **Compliance:** Immutable WORM records, append-only audit trails, SOX/GDPR/7-year retention compliance

---

## Target Users

### Persona 1: Claims Adjuster
**Role:** First-line reviewer for intake validation and assessment approval.  
**Context:** Works 9 AM–6 PM IST, 5 days/week. Handles 40–60 claims per day.  
**Pain Points:**
- Manual checklist verification is tedious and error-prone
- Reason codes are inconsistent; policy-derived codes would standardize decisions
- Manual settlement calculations introduce errors

**Success Criteria:**
- Automated document checklist validation (red/green flags for missing docs)
- Policy-derived reason codes in decision UI (e.g., "Deductible > Premium," "Injury outside policy period")
- Auto-computed payables shown before approval (no manual math)

### Persona 2: Fraud Screener
**Role:** Risk analyst who flags high-risk claims before assessment.  
**Context:** Reviews claims during intake or assessment phase. Preventive role.  
**Pain Points:**
- Subjective fraud assessment leads to inconsistent risk scoring
- No deterministic thresholds; relies on experience and intuition
- High false-negative rate (risky claims approved)

**Success Criteria:**
- Instant deterministic rule scoring against policy fraud thresholds
- Clear pass/fail rules (e.g., "claim amount > 5x average for this policy type" = flag)
- No subjective guesswork; rules are reproducible and auditable

### Persona 3: Settlement Officer / Admin
**Role:** Manages payouts and overrides; ensures compliance and audit integrity.  
**Context:** Works 9 AM–6 PM IST. Authorized to override fraud rejections, initiate reopens, and audit claim mutations.  
**Pain Points:**
- Unsupervised admin access creates compliance exposure (who changed what, when?)
- Payout records can be mutated, breaking immutability for audit
- No way to trace authorization for overrides

**Success Criteria:**
- Immutable payout records matching assessed amounts
- Override capability with mandatory reason code + comment + actor ID + UTC timestamp
- Full audit trail of all mutations; no unauthorized changes possible

### Persona 4: Customer (Self-Service)
**Role:** Policyholder filing FNOL and tracking claim status.  
**Context:** 24/7 access via web portal. Non-technical.  
**Pain Points:**
- No visibility into claim status; calls to adjusters for updates
- Unclear what documents are needed; repeated uploads
- No ability to reopen or dispute a decision

**Success Criteria:**
- File FNOL with policy#, incident date, claim type, document upload
- Track claim status in real-time (status, reason codes, missing docs)
- Initiate dispute or reopen claim (linked sub-claim)

---

## Success Metrics

| Metric | Baseline | Target | Owner |
|--------|----------|--------|-------|
| Processing Time (Auto-Approved) | 5–7 days | < 1 hour | Adjuster, System |
| Processing Time (Manual) | 5–7 days | < 24 hours | Adjuster |
| Fraud Rule Enforcement | ~70% (subjective) | 100% (deterministic) | Fraud Screener, System |
| Cost per Claim | $45 | < $10 @ 10k/month | Operations |
| Calculation Accuracy | 85% (rounding errors) | 100% (deterministic) | System |
| Compliance Violations | 3–5/audit | 0 (immutable WORM) | Compliance, System |
| System Uptime (Business Hours) | N/A | 99.9% | Operations |
| Health Check Response | N/A | < 1 second | Operations |

---

## Scope

### In Scope (MVP)

**Core Workflow Stages:**
1. Intake & Document Upload (S-001)
2. Document Validation (S-002)
3. Fraud Screening (S-003)
4. Assessment & Calculation (S-004)
5. Decisioning & Approval (S-005)
6. Settlement & Payout (S-006)

**Lines of Business (All Three):**
- Motor: FIR + invoice verification
- Health: Hospital bill + discharge summary verification
- Life: Death certificate verification

**User Roles:**
- Adjuster (intake, validation, assessment approval)
- Fraud Screener (fraud rule scoring)
- Settlement Officer / Admin (payout, override, audit)
- Customer (self-service FNOL filing, tracking, reopen)

**Key Features:**
- Policy-derived fraud thresholds and reason codes
- Deterministic rule engine (no ML, no subjective scoring)
- Append-only (WORM) claim, fraud, assessment, and payout records
- Override audit trail (actor ID, reason, timestamp)
- Reopening of settled claims into linked sub-claims (AC-08)
- Health check endpoint

**Regulatory & Compliance:**
- GDPR/DPDP compliance (PII/health data redaction)
- SOX compliance (immutable WORM records)
- 7-year regulatory retention standard
- Append-only audit logs with correlation IDs

### Out of Scope (Future or Explicit Exclusions)

- **Real OCR:** Document verification is rule-based checklist, not image ML
- **ML-Based Fraud:** Fraud screening is deterministic rules only
- **Real Banking/Payment:** Payout is recorded as pending-disbursement; no integration with actual bank transfers
- **Live Hospital/Cashless Workflows:** No integration with hospital systems or cashless claim processors
- **Bureau Integrations:** No connections to credit bureaus, police, or third-party risk agencies
- **Subrogation:** No recovery workflows or subrogation tracking
- **Production Cloud Infrastructure:** Deployment is local/Docker Compose for MVP. Cloud hosting is future phase
- **Real-Time Notifications:** Customer portal updates are polled, not pushed

---

## MVP Definition

The MVP is the smallest deployable slice that delivers measurable value:

**Core Deliverable:**
A single unified claims pipeline that accepts a policyholder's FNOL (policy#, incident, docs) and produces an immutable, audited settlement decision and payout record within 24 hours, with 100% deterministic fraud rule enforcement.

**Staged Sprints:**

| Sprint | Features | Acceptance Gate |
|--------|----------|-----------------|
| Sprint 1 (Days 1–3) | FNOL intake (file claim, upload docs) + document validation (checklist vs. LOB) | Claim record created, docs verified or flagged |
| Sprint 2 (Days 4–6) | Fraud screening (deterministic rule scoring) + assessment & calculation (payables computed) | Fraud score recorded, settlement amount calculated, assessment audit trail |
| Sprint 3 (Days 7–9) | Decisioning (adjuster approval/rejection) + payout settlement (immutable record) + reopen (sub-claim) | Payout record immutable, override audit trail present, reopened claims linked |

**Evaluation Gate (Hours 19–20):**
- All acceptance criteria pass
- Deterministic rules enforced (no fraud threshold violations)
- Audit trail complete and immutable
- Health check returns 200 within 1 second

---

## Alternatives Considered

### Alternative 1: Outsource to Third-Party Claims Platform
**Description:** Integrate with a vendor claims management system (e.g., Sapiens, Duck Creek).  
**Advantages:**
- Vendor handles ongoing support and compliance updates
- Reduced internal development cost
- Vendor has battle-tested fraud rules

**Disadvantages:**
- High licensing cost (~$200k+ annually)
- Vendor lock-in; difficult to customize
- Long onboarding (6–12 months)
- Deterministic rule tuning still requires domain expertise

**Verdict:** Rejected. 20-hour cohort timeline and internal determinism requirements (fraud rules locked at intake time) require custom build.

### Alternative 2: In-House Rules Engine + Off-Shelf Workflow Orchestrator (Temporal, Airflow)
**Description:** Custom fraud rules engine with orchestration via Temporal or Airflow.  
**Advantages:**
- Decoupled rules from workflow
- Orchestrator handles complex state transitions
- Scalable to multi-agent workflows

**Disadvantages:**
- Additional operational complexity (Temporal/Airflow deployment, debugging)
- Overkill for deterministic, linear pipeline (6 sequential stages)
- Non-deterministic orchestrator semantics conflict with rule pinning at intake
- 20-hour timeline too tight for new service learning curve

**Verdict:** Rejected. Custom domain-driven state machine is simpler, more deterministic, and faster to deliver.

### Alternative 3: Custom Domain-Driven State Machine (Chosen)
**Description:** Build a single-service Python + FastAPI application with custom state machine logic, append-only WORM database, and deterministic rule evaluation.  
**Advantages:**
- Determinism: rules pinned at intake; in-flight claims preserve consistency
- Simplicity: single codebase, single deployment, fast local dev (single command)
- Auditability: WORM persistence with immutable records
- Speed: 20-hour timeline achievable

**Disadvantages:**
- Scaling to multi-service later requires refactoring
- No vendor support; ops owned entirely by Horizon

**Verdict:** Chosen. Optimal for MVP timeline, determinism requirements, and local deployment.

---

## Technical Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  (FNOL Filing | Tracker | Reopen | Admin Overrides)    │
└─────────────────────────────────────────────────────────┘
                          ↓ REST API
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend (Python)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ API Endpoints (CRUD for claims, docs, rules)    │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Domain Services (StateMachine, Fraud, Payout)   │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Rule Engine (Deterministic fraud/threshold)     │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Audit & Logging (Correlation ID, Actor, UTC)    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         SQLite / PostgreSQL Database                    │
│  (Append-Only, WORM, Immutable Records)                │
│  Tables: claims, documents, fraud_scores,              │
│          assessments, payouts, override_audit_log       │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Python + FastAPI | Fast dev, async I/O, minimal boilerplate, great for MVP |
| Frontend | React + Tailwind CSS | Fast local dev, responsive UI, no build complexity for eval |
| Database | SQLite (dev) / PostgreSQL (test) | SQLite for single-command local startup; PG for immutability guarantees |
| State Machine | Custom Domain-Driven | Explicit transitions, deterministic, auditable |
| Authentication | Role-Based Access Control (RBAC) | Adjuster, Fraud Screener, Admin, Customer roles |
| Audit Trail | Append-Only Event Log | Immutable, correlation-tracked, actor/timestamp |

### State Machine

**Claim States:**
```
FILED 
  ↓ (document validation)
UNDER_REVIEW 
  ↓ (fraud scoring + assessment)
APPROVED or REJECTED 
  ↓ (settlement)
SETTLED 
  ↓ (optional)
REOPENED (linked sub-claim created)
```

**Invalid Transitions:**
- APPROVED → FILED (re-intake not allowed once approved)
- REJECTED → SETTLED (cannot payout a rejected claim)
- Any transition without rule validation raises `InvalidClaimStateException`

**Override Logic:**
- Only Admin can transition REJECTED → SETTLED with override
- Override requires: reason code, comment, actor ID, UTC timestamp
- Override audit entry is immutable

---

## Data Model Overview

### Core Entities

**Policy**
- `policy_id` (UUID, PK)
- `policy_number` (string, unique)
- `customer_id` (UUID, FK to Customer)
- `line_of_business` (enum: MOTOR, HEALTH, LIFE)
- `coverage_amount` (decimal, non-nullable)
- `deductible` (decimal)
- `co_pay_percent` (decimal)
- `active_rule_version_id` (UUID, FK to FraudRuleVersion)
- `effective_date` (timestamp)
- `expiry_date` (timestamp, nullable)
- `created_at` (timestamp, immutable)

**Claim**
- `claim_id` (UUID, PK)
- `policy_id` (UUID, FK to Policy)
- `customer_id` (UUID, FK to Customer)
- `claim_state` (enum: FILED, UNDER_REVIEW, APPROVED, REJECTED, SETTLED, REOPENED)
- `line_of_business` (enum: MOTOR, HEALTH, LIFE)
- `incident_date` (timestamp)
- `incident_description` (text, redacted in logs)
- `policy_rule_version_id` (UUID, FK to FraudRuleVersion; pinned at intake)
- `created_at` (timestamp, immutable)
- `updated_at` (timestamp, updated only to reflect state transitions)

**Document**
- `document_id` (UUID, PK)
- `claim_id` (UUID, FK to Claim)
- `document_type` (enum: FIR, INVOICE, HOSPITAL_BILL, DISCHARGE_SUMMARY, DEATH_CERTIFICATE)
- `file_name` (string)
- `file_url` (string, redacted in logs)
- `uploaded_at` (timestamp, immutable)
- `verified` (boolean, immutable once set)
- `verified_by_adjuster_id` (UUID, FK to User)
- `verified_at` (timestamp, immutable)

**FraudScreeningResult**
- `fraud_result_id` (UUID, PK)
- `claim_id` (UUID, FK to Claim)
- `rule_version_id` (UUID, FK to FraudRuleVersion)
- `fraud_score` (decimal, 0.0–1.0)
- `fraud_rules_triggered` (JSON array of rule names and thresholds)
- `is_flagged` (boolean: true if score >= policy threshold)
- `evaluated_at` (timestamp, immutable)
- `evaluated_by_system` (boolean; true if automatic, false if manual override)

**Assessment**
- `assessment_id` (UUID, PK)
- `claim_id` (UUID, FK to Claim)
- `assessed_amount` (decimal, deterministically calculated)
- `payable_amount` (decimal, after deductible/co-pay)
- `deductible_applied` (decimal)
- `co_pay_applied` (decimal)
- `reason_code` (enum: policy-derived, e.g., "DEDUCTIBLE_EXCEEDED", "PARTIAL_COVERAGE")
- `assessed_by_adjuster_id` (UUID, FK to User)
- `assessed_at` (timestamp, immutable)

**Settlement**
- `settlement_id` (UUID, PK)
- `claim_id` (UUID, FK to Claim)
- `payout_amount` (decimal, matches assessment payable_amount)
- `payout_state` (enum: PENDING_DISBURSEMENT, DISBURSED, FAILED_RETRY)
- `approved_by_admin_id` (UUID, FK to User)
- `approved_at` (timestamp, immutable)
- `disbursed_at` (timestamp, nullable, immutable once set)

**OverrideAuditLog**
- `override_id` (UUID, PK)
- `claim_id` (UUID, FK to Claim)
- `override_type` (enum: FRAUD_REJECTION_OVERRIDE, STATE_TRANSITION_OVERRIDE)
- `previous_state` (enum, e.g., REJECTED)
- `new_state` (enum, e.g., SETTLED)
- `reason_code` (string)
- `comment` (text, redacted in logs)
- `actor_id` (UUID, FK to User; admin who authorized override)
- `actor_email` (string; immutable audit trail)
- `override_at` (timestamp, immutable, UTC)

**SubClaim**
- `sub_claim_id` (UUID, PK)
- `parent_claim_id` (UUID, FK to Claim)
- `sub_claim_type` (enum: DISPUTE, REOPEN)
- `reason` (text)
- `created_by_customer_id` (UUID, FK to Customer)
- `created_at` (timestamp, immutable)
- New claim state: FILED (inherits policy/rules from parent)

**FraudRuleVersion**
- `rule_version_id` (UUID, PK)
- `version_number` (integer, auto-increment)
- `line_of_business` (enum: MOTOR, HEALTH, LIFE)
- `rules` (JSON: array of { rule_name, threshold, operator, field })
  - Example: `{ "rule_name": "claim_exceeds_avg", "threshold": 5, "operator": ">=", "field": "claim_amount / avg_policy_claim" }`
- `effective_date` (timestamp)
- `created_at` (timestamp, immutable)
- `created_by_admin_id` (UUID, FK to User)

**User**
- `user_id` (UUID, PK)
- `email` (string, unique, immutable)
- `role` (enum: ADJUSTER, FRAUD_SCREENER, ADMIN, CUSTOMER)
- `created_at` (timestamp, immutable)

---

## External Integrations

**None for MVP.** All integrations are out of scope:
- No live policy API (policies seeded in repository)
- No banking/payment gateway (payout recorded as pending)
- No hospital/cashless claim processors
- No bureau integrations (credit, police, third-party)
- No notification service (customers check portal)

---

## Edge Cases & Constraints

### Edge Case 1: Fraud Rule Version Change During In-Flight Claim
**Scenario:** Policy fraud rules are updated (e.g., new threshold) while a claim is mid-assessment.  
**Handling:** Claim's `policy_rule_version_id` is pinned at intake time (FILED state). In-flight claims always use the pinned rule version. New claims use the active version. Ensures determinism and auditability.

### Edge Case 2: Payout Disbursement Failure
**Scenario:** System crashes after payout settlement is committed to DB but before payment is sent.  
**Handling:** Payout record is immutable and remains in `PENDING_DISBURSEMENT` state. On system recovery, retry is idempotent (same `settlement_id`, same `payout_amount`). No rollback or duplicate payout.

### Edge Case 3: Admin Override of Fraud-Rejected Claim
**Scenario:** Fraud screener flags a claim as high-risk; admin wants to approve anyway.  
**Handling:** Only Admin role can override. Override requires:
- Mandatory reason code (enum: e.g., "LEGITIMATE_HIGH_VALUE", "SPECIAL_CIRCUMSTANCE")
- Mandatory comment (free text)
- System auto-captures actor ID and UTC timestamp
- Override entry is immutable in OverrideAuditLog

### Edge Case 4: Reopening a Settled Claim
**Scenario:** Customer disputes settlement or claim reopens due to new information.  
**Handling:** Reopening creates a linked sub-claim (SubClaim record) with parent_claim_id. Sub-claim enters FILED state and flows through pipeline again independently. Parent claim remains SETTLED and immutable; sub-claim audit trail is separate.

### Edge Case 5: Multi-Document Motor Claim (FIR + Invoice + Photo)
**Scenario:** Motor claim requires FIR, invoice, and police report. System must handle partial uploads.  
**Handling:** Documents are individually verified or flagged. Claim state remains UNDER_REVIEW until all required documents pass verification checklist. If any document fails verification, adjuster is prompted for missing docs.

### Edge Case 6: PII & Health Data Redaction in Logs
**Scenario:** Claim for health insurance includes hospital bill with patient name, diagnosis, procedure costs.  
**Handling:** Hospital bill `file_url` and claim `incident_description` are redacted in all logs (replaced with [REDACTED]). Audit logs record the action (e.g., "Document verified") but not the content. Only adjuster UI shows raw data (within role-based access control).

### Edge Case 7: Customer Self-Service Viewing Redacted Data
**Scenario:** Customer accesses claim tracker via self-service portal. Should they see full incident narrative?  
**Handling:** Customer self-service portal shows claim status, reason codes, missing docs, payable amount. Incident narrative and document content are not shown (GDPR/DPDP compliance). If customer disputes, they file via reopen flow and support team reviews.

---

## Compliance & Audit Requirements

### GDPR / DPDP Compliance (NFR-03)
- PII and health data are never logged in plaintext
- Document content and claim narratives redacted in structured logs
- Logs show action (e.g., "Document verified") but not content
- 7-year retention: archived logs encrypted and retained per regulation
- Right to deletion: Manual admin process (future phase)

### SOX Compliance (NFR-02, NFR-05)
- All claim, fraud, assessment, and payout records are append-only (WORM)
- No deletion or mutation of settled records
- Override audit log captures: actor, reason, timestamp, previous/new state
- Reconciliation: all payouts must match assessment amounts (deterministic calculation)
- 7-year retention standard for all claim and audit records

### Audit Trail (NFR-04)
- All mutations captured: claim state transitions, fraud scores, assessments, overrides
- Audit entry includes: actor_id, actor_email, timestamp (UTC), operation, reason_code
- Correlation IDs link related operations across services
- Logs are immutable and timestamped

### Health Check SLA (NFR-07)
- Endpoint: `GET /health`
- Response: HTTP 200 + JSON `{ "status": "ok" }`
- SLA: Response within 1 second of startup
- Used for operational monitoring and readiness checks

---

## UI Context

### Customer Self-Service Portal

**Screen 1: File FNOL**
- Input fields: Policy#, Incident Date, Claim Type (MOTOR/HEALTH/LIFE), Description
- Document upload: Multi-file upload based on claim type (e.g., FIR + invoice for motor)
- Submit: Creates claim in FILED state
- Confirmation: Claim ID and next steps

**Screen 2: Claim Tracker**
- Claim summary: Claim ID, status (FILED, UNDER_REVIEW, APPROVED, REJECTED, SETTLED, REOPENED)
- Status timeline: Intake → Validation → Fraud Check → Assessment → Decision → Payout
- Missing docs: If in UNDER_REVIEW, shows list of required but missing documents
- Reason codes: If APPROVED, shows reason (e.g., "FULL_COVERAGE_APPROVED"). If REJECTED, shows reason (e.g., "OUTSIDE_POLICY_PERIOD")
- Payable amount: If APPROVED, shows expected payout

**Screen 3: Dispute / Reopen**
- Link: Available if claim is SETTLED
- Input: Reason (enum: DISPUTE, REOPEN; free-text explanation)
- Submit: Creates sub-claim (FILED state), notifies support
- Confirmation: Sub-claim ID and next steps

**Design Principles:**
- Responsive: Desktop, tablet, mobile viewports
- Accessibility: WCAG AA (headings, form labels, color contrast)
- Clarity over polish: Functional UI; high-end design not required
- No custom fonts or animations; standard Bootstrap/Tailwind styling

### Internal Admin Portal

**Screens for Adjuster:**
- Intake Verification: Checklist of required docs, verified/flagged status
- Assessment: Auto-computed payable amount, reason code selector, approve/reject
- Reason codes: Policy-derived (e.g., "DEDUCTIBLE_EXCEEDED", "PARTIAL_COVERAGE")

**Screens for Fraud Screener:**
- Fraud Queue: List of claims pending fraud review
- Fraud Score: Deterministic score (0.0–1.0), rules triggered, pass/fail decision
- No subjective override; only system-calculated score shown

**Screens for Settlement Officer/Admin:**
- Settlement Queue: Claims ready for payout
- Payout Details: Settlement amount, account for disbursement, approval button
- Override Capability: Link to override rejected claims; requires reason code + comment
- Audit Log: Immutable log of all mutations (actor, reason, timestamp)

---

## Deployment & Operations

### Local Development

**Single-Command Startup:**
```bash
# Backend
uvicorn main:app --reload

# Frontend (separate terminal)
npm start

# Or via Docker Compose
docker-compose up
```

**Seed Data:**
- `seeds/policies.json` — Motor, health, life policies with fraud thresholds
- `seeds/fraud_rules.json` — Deterministic fraud rules per LOB
- `seeds/users.json` — Test users (adjuster, fraud screener, admin, customers)

**Database:**
- SQLite for local dev (file-based, zero setup)
- PostgreSQL for test/CI environments

### Logging & Monitoring

**Structured Logging:**
```json
{
  "timestamp": "2026-10-04T14:30:00Z",
  "correlation_id": "claim-abc123-event-001",
  "action": "claim_state_transition",
  "actor_id": "user-adj-001",
  "actor_role": "ADJUSTER",
  "claim_id": "claim-abc123",
  "previous_state": "FILED",
  "new_state": "UNDER_REVIEW",
  "reason_code": "DOCS_VERIFIED"
}
```

**Redacted Logs:**
- PII: [REDACTED]
- Health records: [REDACTED]
- Document content: [REDACTED]
- Claim narrative: [REDACTED]

**Health Check:**
- Endpoint: `GET /health`
- Response: `{ "status": "ok", "timestamp": "2026-10-04T14:30:00Z" }`
- Frequency: Operations team polls every 60 seconds (production target)

### Backup & Recovery (Future Phase)

**MVP (Local):**
- SQLite file backed up locally
- Append-only migrations tracked in version control

**Production Targets:**
- RPO (Recovery Point Objective): < 15 minutes (hourly snapshots)
- RTO (Recovery Time Objective): < 1 hour (restored from snapshot)
- Immutable write-once audit structures ensure no accidental mutation on restore

---

## Timeline & Release Plan

### Hard Deadline
**Within 20-hour cohort evaluation window (2026-10-04, hours 19–20 UTC).**

### Sprint Breakdown

| Sprint | Duration | Focus | Acceptance Gate |
|--------|----------|-------|-----------------|
| Sprint 1 | Days 1–3 (Hrs 0–9) | Intake + Validation | Claim filed, docs verified, UNDER_REVIEW state |
| Sprint 2 | Days 4–6 (Hrs 9–18) | Fraud + Assessment | Fraud score recorded, payables calculated, assessment audit trail |
| Sprint 3 | Days 7–9 (Hrs 18–20) | Settlement + Reopen | Payout immutable, override audit present, sub-claim linked |
| Evaluation | Hours 19–20 | Test all acceptance criteria, demo to stakeholder | All ACs pass, health check 200 within 1s, zero violations |

### Operational Release Target
**Q4 2026** (after cohort evaluation success)
- Beta: Internal adjuster team (10–20 claims/day)
- Ramp: Full adjuster team (100–200 claims/day)
- Production: 10k claims/month steady-state

---

## Assumptions

1. **Policies and Fraud Rules:** Policies and fraud rule versions are seeded in the repository as JSON/YAML; no live policy API required.
2. **Deterministic Fraud Rules:** Fraud rules are entirely deterministic (e.g., thresholds, field comparisons). No ML or subjective scoring.
3. **Role-Based Access Control:** RBAC is implemented via in-memory role checks (not LDAP or SSO). Test users are hard-coded for MVP.
4. **Document Verification:** Document validation is rule-based checklist (e.g., "Motor claim must have FIR + invoice"), not OCR or image analysis.
5. **Payout Idempotency:** Payout disbursement is recorded but not actually sent to bank; idempotency is assumed for retry logic.
6. **7-Year Retention:** Compliance team manages archival and deletion separately; system assumes all records are retained indefinitely for MVP.
7. **Correlation ID Propagation:** All API requests and log entries include a correlation ID; tracing is end-to-end but not aggregated externally.
8. **UTC Timestamps:** All timestamps are UTC; no timezone conversion in MVP.

---

## Open Questions

1. **Customer Notification:** Should customers receive email/SMS notifications when claim status changes, or is portal polling sufficient for MVP?
2. **Dispute Resolution:** If a customer reopens a claim, what is the SLA for support team review?
3. **Fraud Rule Tuning:** Who owns updating fraud thresholds after MVP launch? Is there a manual admin process or automated tuning?
4. **Concurrent Claims:** Can a single customer file multiple claims in parallel? Are they independent or linked?
5. **Escalation Path:** What is the process if an adjuster is unsure about a decision (e.g., borderline fraud score)?
6. **Multi-Language Support:** Is the portal required to support languages beyond English?
7. **Mobile App:** Is a native mobile app required, or is a responsive web portal sufficient?
8. **Real Payout Integration:** When will real bank integration be added (Phase 2)?

---

## Regulatory & Compliance Sign-Off

- **GDPR/DPDP:** Health data and PII redacted in logs; retention policy documented ✓
- **SOX:** Append-only WORM persistence; override audit trail immutable ✓
- **7-Year Retention:** All records archived; deletion process documented (future phase) ✓
- **Role-Based Access Control:** Adjuster, Fraud Screener, Admin, Customer roles enforced ✓
- **Audit Trail:** All mutations captured with actor ID, reason code, UTC timestamp ✓

**Compliance Review Status:** Ready for legal and audit team review.

---

## Sign-Off

**Prepared by:** Planner Agent (Claude Harness Engine)  
**Date:** 2026-10-04  
**Status:** Approved for `/spec` phase

**Next Steps:**
- Human stakeholder review and approval
- Proceed to `/spec` command for user story decomposition and dependency graph
- Generate `features.json` for sprint backlog

