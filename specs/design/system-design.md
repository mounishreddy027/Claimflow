# ClaimFlow System Design

AI-native claims management platform automating the FNOL-to-settlement pipeline with deterministic fraud screening, assessment calculation, and immutable payouts.

## Architecture Overview

### Layered Architecture (Strict One-Way Dependencies)

```
UI Layer (React + Tailwind)
    ↓ (calls only)
API Layer (REST endpoints, request validation, auth, correlation IDs)
    ↓ (calls only)
Service Layer (business logic, fraud engine, payout calculation, assessments)
    ↓ (calls only)
Repository Layer (persistence, WORM enforcement, audit trail)
    ↓ (calls only)
Config Layer (checklists, fraud rules, policy rules, versioned)
    ↓ (reads)
Type Layer (data contracts, enums, exceptions)
```

Each layer depends only on layers below it. No reverse dependencies. No horizontal dependencies.

### Core Components

**Backend (Python)**
- uv package manager, pytest testing, ruff linting, mypy static typing
- FastAPI REST server
- SQLAlchemy ORM with immutability constraints
- PostgreSQL database with audit trails and WORM enforcement

**Frontend (Node.js)**
- React with TypeScript
- Tailwind CSS for styling
- Playwright E2E tests
- npm package management

**Infrastructure**
- Docker Compose for orchestration
- PostgreSQL for persistent storage
- File storage for document uploads
- Audit trail database for compliance

### Key Design Decisions

**Deterministic Processing Only**
- No ML models, no probabilistic fraud scoring
- All rules are deterministic predicates evaluated against claim attributes
- Rule versioning ensures identical in-flight claims use the same rule version pinned at intake
- Financial calculations use fixed-point arithmetic (2 decimal places minimum)

**Immutability & WORM**
- Claims are filed once and never deleted
- Settlement records are append-only; once created, fields cannot be modified
- Audit trail is immutable for SOX/regulatory compliance
- Overrides create new audit entries; original decisions are never erased

**Deterministic Fraud Scoring**
- Fraud rules are versioned configurations loaded at startup
- Each claim pins its rule version at intake (E1-S2)
- Fraud screening evaluates deterministic predicates: `claim_amount > threshold`, etc.
- Fraud score is sum of triggered rule weights, clamped to [0, 100]

**Financial Invariants**
- `payable_amount = min(claim_amount, sum_insured) - deductible - co_pay`
- `payable_amount >= 0` is always enforced (clamped to 0 if calculation goes negative)
- Fixed-point arithmetic prevents rounding errors
- Settlement payout exactly matches assessment payable amount (no adjustment)

**Immutable Settlement Ledger**
- Settlements are created as PENDING_DISBURSEMENT
- Records cannot be modified once created (database constraints + app logic)
- Override scenarios create new settlement entries with separate OverrideAuditLog
- 7-year retention for SOX compliance

**State Machine Governance**
Claim lifecycle: FILED → UNDER_REVIEW → APPROVED/REJECTED → SETTLED/CLOSED

State transitions:
- FILED → UNDER_REVIEW: after document verification passes
- UNDER_REVIEW → APPROVED: after assessment decision
- UNDER_REVIEW → REJECTED: after assessment decision
- APPROVED → SETTLED: after settlement confirmation
- REJECTED → APPROVED: only via admin override (rare)
- SETTLED → REOPENED (status flag): when sub-claim created
- Any state → CLOSED: after 7-year retention period or customer request

**Policy Rule Version Pinning**
- Fraud rules: pinned at claim intake (E1-S2)
- Coverage rules: evaluated against policy at intake
- Assessment rules: applied using pinned fraud rule version
- Ensures determinism: same claim evaluated multiple times always produces same fraud score

**Document Verification Workflow**
- Checklists defined per LOB: Motor, Health, Life
- Documents marked PENDING_VERIFICATION on upload
- Claims cannot transition from FILED to UNDER_REVIEW until all required documents verified
- Verification decision (VERIFIED/REJECTED) is immutable

**Audit Trail & Compliance**
- Every state transition logged with actor, timestamp, correlation ID, and context
- Sensitive data (PII, health info) redacted in audit logs
- Append-only: audit entries cannot be modified or deleted
- Queries support filtering by claim_id, actor_id, operation_type, timestamp range
- Endpoint `GET /api/audit-trail/{claim_id}` provides complete history per claim

**Role-Based Access Control (RBAC)**
- ROLE_CUSTOMER: sees claim status, redacted incident details, payable amounts
- ROLE_ADJUSTER: sees full claim details, fraud scores, assessment data, document verification queue
- ROLE_ADMIN: can override decisions, generate settlements, access audit trails
- Authentication via correlation ID and actor role in every request

**Sub-Claim & Dispute Handling**
- Settled claims can be reopened via sub-claims (child claims)
- Sub-claims inherit policy and rule versions from parent
- Parent claim remains SETTLED and immutable; only status flag updated
- Sub-claims flow through pipeline independently starting from FILED
- Maximum one override per claim; OverrideAuditLog tracks all overrides immutably

---

## Technology Stack

**Backend**
- Language: Python 3.11+
- Framework: FastAPI
- ORM: SQLAlchemy with psycopg2 adapter
- Testing: pytest with fixtures and mocking
- Linting: ruff for style and import sorting
- Type Checking: mypy for static analysis
- Database: PostgreSQL 14+

**Frontend**
- Language: TypeScript 5+
- Framework: React 18+
- Styling: Tailwind CSS
- Testing: Playwright for E2E
- Build: npm/Node.js
- State Management: Context API or Redux (TBD)

**Infrastructure**
- Containerization: Docker, Docker Compose
- File Storage: Local filesystem (MVP), S3 (future)
- Secrets: Environment variables, no hardcoded credentials
- CI/CD: GitHub Actions (future)
- Monitoring: Structured logging, correlation IDs for tracing

---

## Data Flow

### Claim Intake Flow (E1-S2)
```
Customer submits FNOL
    ↓
POST /api/claims/intake
    ↓
Validate policy active (E1-S1)
    ↓
Lookup fraud rule version (E3-S2)
    ↓
Create Claim (FILED state)
    ↓
Pin fraud rule version to claim
    ↓
Return claim_id + correlation_id
```

### Document Verification Flow (E2-S2 → E2-S4)
```
Customer uploads documents
    ↓
POST /api/claims/{claim_id}/documents
    ↓
Store document (PENDING_VERIFICATION)
    ↓
GET /api/document-verification-queue
    ↓
Adjuster reviews documents
    ↓
POST /api/claims/{claim_id}/verify-documents
    ↓
Check all required docs verified
    ↓
Transition claim to UNDER_REVIEW
```

### Fraud Screening → Assessment → Settlement Flow (E3-S3 → E4-S3 → E5-S3)
```
POST /api/claims/{claim_id}/evaluate-fraud
    ↓
Apply fraud rules (E3-S1)
    ↓
Record FraudScreeningResult
    ↓
If flagged: claim stays UNDER_REVIEW for manual review
    ↓
POST /api/claims/{claim_id}/assess
    ↓
Calculate payout (E4-S2)
    ↓
Record Assessment (APPROVED/REJECTED/MANUAL_REVIEW)
    ↓
If APPROVED:
    POST /api/claims/{claim_id}/settle
    ↓
Generate settlement (E5-S2)
    ↓
Record Settlement (immutable, PENDING_DISBURSEMENT)
    ↓
Transition claim to SETTLED
```

### Admin Override Flow (E7-S1 → E7-S3)
```
Admin submits override
    ↓
POST /api/claims/{claim_id}/override-decision
    ↓
Verify admin role (AC-09)
    ↓
Validate override eligibility (no prior overrides)
    ↓
Create OverrideAuditLog entry (immutable)
    ↓
Transition claim state
    ↓
If REJECTED → APPROVED: generate settlement (E5-S2)
    ↓
Return updated claim + settlement details
```

### Dispute & Sub-Claim Flow (E6-S1 → E6-S2)
```
Customer disputes settled claim
    ↓
POST /api/claims/{parent_claim_id}/dispute
    ↓
Create SubClaim record (DISPUTE type)
    ↓
Create linked child Claim (FILED state)
    ↓
Inherit policy + fraud rule version from parent
    ↓
Parent remains SETTLED; status flag → REOPENED
    ↓
Child claim flows through pipeline independently
```

---

## Database Design Principles

**Immutability Enforcement**
- Immutable fields use NOT NULL + database triggers to prevent UPDATE
- DELETE operations blocked by application and foreign key constraints
- Soft deletes never used; history preserved via audit trail only

**Audit Trail Persistence**
- Every operation recorded: actor, timestamp (UTC), correlation_id, operation_type, context
- Sensitive fields (PII, health data, URLs) redacted with `[REDACTED]` marker
- Queries support filtering by claim_id, actor_id, timestamp range, operation_type

**Financial Data Storage**
- NUMERIC(10, 2) type for all monetary values (2 decimal precision minimum)
- No floating-point types for financial calculations
- Intermediate calculations maintain full precision until final rounding

**Versioning & Configuration**
- Fraud rules: version number, effective_date, created_by_admin_id, is_active flag
- Coverage rules: similar versioning scheme
- Policy definitions: versioned in database; claims pin version at intake
- Document checklists: versioned per LOB

---

## Compliance & Security

**SOX Compliance**
- Immutable audit trail for all material operations
- 7-year retention of settlement and audit records
- No deletion of historical data (only archive after 7 years)

**GDPR Compliance**
- PII redacted in audit logs (customer name → `[REDACTED]`)
- Right to be forgotten: anonymize personal data (no deletion of transaction records)
- Data portability: export API for customer data

**Financial Invariants**
- Payable amount always >= 0 (clamped to 0 if calculation negative)
- Settlement amount exactly matches assessment payable amount (no rounding adjustment)
- Fixed-point arithmetic for all monetary calculations

**Role-Based Access Control**
- ROLE_CUSTOMER: read own claims only, no access to admin operations
- ROLE_ADJUSTER: read/write document verification, fraud evaluation, assessment
- ROLE_ADMIN: override decisions, manage fraud rules, access audit trails
- Authentication: actor_id + role in every API request; correlation ID for tracing

**Security**
- No hardcoded credentials (env vars only)
- HTTPS for all API traffic (enforced in deployment)
- Request validation: accept only expected fields, reject unknown fields
- CORS: whitelist frontend origin only
- Rate limiting: 100 requests per minute per user (configurable)

---

## Scalability & Performance

**API Response Times**
- Claim intake: < 200ms (policy validation + fraud rule pinning)
- Fraud evaluation: < 500ms (rule engine execution)
- Assessment decision: < 300ms (payout calculation)
- Settlement confirmation: < 200ms (immutable record creation)

**Database Indexing**
- claim_id: primary key, indexed for fast lookups
- policy_number: indexed for policy validation
- correlation_id: indexed for audit trail queries
- timestamp: indexed for time-range queries
- actor_id: indexed for audit filtering

**Concurrency**
- Pessimistic locking on claim during state transitions
- Optimistic locking on assessment/settlement records (version fields)
- No concurrent overrides allowed (database unique constraint on claim_id in OverrideAuditLog)

**Batch Operations**
- Document bulk upload: chunked by 5MB per file
- Audit trail export: paginated, 1000 records per page
- Fraud rule updates: background job, no impact on in-flight claims

---

## Testing Strategy

**Unit Tests** (pytest)
- Coverage: 100% for business logic, 80% floor overall
- Policy validation, fraud scoring, payout calculation
- Immutability enforcement, state machine transitions
- Mock external dependencies (policy repository, etc.)

**Integration Tests**
- End-to-end API flows: intake → assessment → settlement
- Database immutability constraints
- Audit trail recording
- Policy version pinning

**E2E Tests** (Playwright)
- Customer claim intake flow
- Document upload and verification
- Assessment decision workflow
- Admin override scenario

---

## Deployment Architecture

**Development**
- Docker Compose: backend (FastAPI), frontend (React dev server), PostgreSQL
- init.sh script: initialize database, run migrations, seed test data
- Hot reload: backend via Python, frontend via npm dev server

**Staging/Production**
- Kubernetes or Docker Compose (MVP uses Docker Compose)
- PostgreSQL 14+ with automated backups
- Immutability constraints enforced at database level
- Secrets management: AWS Secrets Manager or HashiCorp Vault

**CI/CD**
- GitHub Actions (future)
- Run pytest, ruff, mypy on push
- Build Docker images
- Deploy to staging on PR approval
- Deploy to prod with manual approval

---

## Open Questions / Future Enhancements

1. **Payment Gateway Integration** — Actual bank transfers for disbursement (E5 MVP stops at PENDING_DISBURSEMENT)
2. **Document Storage Backend** — MVP uses local filesystem; production should use S3 or similar
3. **Frontend State Management** — Context API vs Redux decision deferred
4. **Kafka/Message Queue** — For asynchronous settlement disbursement
5. **Multi-region Deployment** — Sync/eventual consistency for audit trail
6. **Machine Learning** — Future enhancement: real ML models alongside deterministic rules
7. **Mobile App** — React Native for claimant mobile filing

---

## Summary

ClaimFlow is a spec-driven, agent-generated claims platform enforcing strict architectural layering, deterministic processing, immutable audit trails, and fixed-point financial calculations. The design supports 21 stories across 7 epics, with zero hand-written production code, built entirely via Claude Code agents with comprehensive testing and compliance guardrails.
