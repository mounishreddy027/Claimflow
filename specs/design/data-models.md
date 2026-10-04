# Data Models — ClaimFlow

Complete data entity specifications with fields, types, constraints, relationships, and indexes.

## Core Entities

### Claim

Primary entity representing a filed insurance claim from FNOL through settlement.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `claim_id` | UUID | PK, NOT NULL | Unique claim identifier |
| `policy_id` | UUID | FK (Policy), NOT NULL | Associated policy |
| `customer_id` | UUID | FK (Customer), NOT NULL | Claimant customer ID |
| `claim_type` | ENUM | IN (MOTOR, HEALTH, LIFE), NOT NULL | Claim classification |
| `line_of_business` | ENUM | IN (MOTOR, HEALTH, LIFE), NOT NULL | Derived from claim_type |
| `claim_state` | ENUM | IN (FILED, UNDER_REVIEW, APPROVED, REJECTED, SETTLED, CLOSED), NOT NULL | Current state in lifecycle |
| `status_flag` | ENUM | IN (NORMAL, REOPENED), default NORMAL | Secondary status (for reopened claims) |
| `incident_date` | TIMESTAMP | NOT NULL, UTC | When incident occurred |
| `incident_description` | TEXT | NOT NULL | Details of incident |
| `created_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Claim filing timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, UTC | Last state transition |
| `policy_rule_version_id` | UUID | FK (FraudRuleVersion), NOT NULL | Fraud rule version pinned at intake |
| `reason_code` | VARCHAR(100) | nullable | Reason for current state (e.g., DOCS_VERIFIED, FRAUD_FLAGGED) |

**Indexes**
- (claim_id): PRIMARY KEY
- (policy_id): for policy lookup
- (customer_id): for customer claims list
- (claim_state): for state filtering
- (created_at): for chronological queries
- (incident_date): for temporal queries

**Constraints**
- NOT NULL on all marked fields
- state_code must be valid transition from previous state
- claim_state cannot be modified to FILED after creation (one-way transitions)
- incident_date <= created_at (incident must precede filing)

**Relationships**
- Policy 1:N Claim (foreign key: policy_id)
- Customer 1:N Claim (foreign key: customer_id)
- Claim 1:N Document (foreign key: claim_id)
- Claim 1:1 Assessment (foreign key: claim_id)
- Claim 1:1 FraudScreeningResult (foreign key: claim_id)
- Claim 1:N Settlement (foreign key: claim_id, max 1 per override scenario)
- Claim 1:N SubClaim (foreign key: related_claim_id or parent_claim_id)
- Claim 1:N AuditLog (foreign key: claim_id)

---

### Policy

Insurance policy master data.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `policy_id` | UUID | PK, NOT NULL | Unique policy identifier |
| `policy_number` | VARCHAR(50) | NOT NULL, UNIQUE | Human-readable policy number |
| `customer_id` | UUID | FK (Customer), NOT NULL | Policy holder |
| `line_of_business` | ENUM | IN (MOTOR, HEALTH, LIFE), NOT NULL | Coverage type |
| `effective_date` | DATE | NOT NULL | Policy inception date |
| `expiry_date` | DATE | nullable | Policy expiration (NULL = lifetime) |
| `sum_insured` | NUMERIC(10,2) | NOT NULL, > 0 | Maximum covered amount |
| `premium_amount` | NUMERIC(10,2) | NOT NULL, >= 0 | Annual/term premium |
| `deductible` | NUMERIC(10,2) | NOT NULL, >= 0 | Deductible per claim |
| `co_pay_percent` | NUMERIC(5,2) | NOT NULL, 0-100 | Co-pay percentage |
| `coverage_exclusions` | JSONB | NOT NULL, default {} | Excluded incident types |
| `created_at` | TIMESTAMP | NOT NULL, UTC | Policy creation |
| `updated_at` | TIMESTAMP | NOT NULL, UTC | Last modification |

**Indexes**
- (policy_id): PRIMARY KEY
- (policy_number): UNIQUE for lookups
- (customer_id): for customer policies
- (effective_date, expiry_date): for date-range queries

**Constraints**
- effective_date <= expiry_date (if expiry_date not NULL)
- sum_insured > 0
- co_pay_percent in range [0, 100]
- deductible >= 0

**Example Record**
```json
{
  "policy_id": "pol-uuid-1",
  "policy_number": "MOTOR-12345",
  "customer_id": "cust-uuid-1",
  "line_of_business": "MOTOR",
  "effective_date": "2025-01-01",
  "expiry_date": "2026-12-31",
  "sum_insured": 100000.00,
  "premium_amount": 5000.00,
  "deductible": 500.00,
  "co_pay_percent": 10.00,
  "coverage_exclusions": {
    "excluded_activities": ["racing", "commercial_use"]
  }
}
```

---

### Document

Uploaded claim supporting documents.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `document_id` | UUID | PK, NOT NULL | Unique document identifier |
| `claim_id` | UUID | FK (Claim), NOT NULL | Associated claim |
| `document_type` | ENUM | IN (POLICE_FIR, REPAIR_INVOICE, HOSPITAL_BILL, DISCHARGE_SUMMARY, DEATH_CERTIFICATE), NOT NULL | Document classification |
| `file_name` | VARCHAR(255) | NOT NULL | Original file name |
| `file_url` | VARCHAR(2048) | NOT NULL | Storage path/URL |
| `file_size_bytes` | INTEGER | NOT NULL, > 0 | Document size |
| `file_hash` | VARCHAR(64) | NOT NULL | SHA-256 hash for integrity |
| `uploaded_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Upload timestamp |
| `verified` | BOOLEAN | default FALSE | Verification status |
| `verified_by_adjuster_id` | UUID | FK (User), nullable | Adjuster who verified |
| `verified_at` | TIMESTAMP | nullable, IMMUTABLE (if set) | Verification timestamp |
| `verification_status` | ENUM | IN (PENDING_VERIFICATION, VERIFIED, REJECTED), default PENDING_VERIFICATION | Verification decision |
| `verification_reason_code` | VARCHAR(50) | nullable | Reason for rejection (e.g., UNREADABLE, INVALID_FORMAT) |

**Indexes**
- (document_id): PRIMARY KEY
- (claim_id): for claim documents
- (document_type): for filtering by type
- (uploaded_at): for chronological queries
- (verified): for unverified document queries

**Constraints**
- NOT NULL on required fields
- file_size_bytes > 0
- file_url immutable after creation
- uploaded_at immutable
- verified_at cannot be changed once set (update trigger enforces)
- Foreign key constraint: claim_id must exist

**Relationships**
- Claim 1:N Document (foreign key: claim_id)

---

### Assessment

Immutable adjudication decision record.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `assessment_id` | UUID | PK, NOT NULL | Unique assessment identifier |
| `claim_id` | UUID | FK (Claim), NOT NULL, UNIQUE | Associated claim (one per claim) |
| `assessed_amount` | NUMERIC(10,2) | NOT NULL, >= 0 | Amount approved for coverage |
| `payable_amount` | NUMERIC(10,2) | NOT NULL, >= 0 | Final payable after deductions |
| `deductible_applied` | NUMERIC(10,2) | NOT NULL, >= 0 | Deductible deducted |
| `co_pay_applied` | NUMERIC(10,2) | NOT NULL, >= 0 | Co-pay deducted |
| `decision` | ENUM | IN (AUTO_APPROVE, MANUAL_REVIEW, REJECT), NOT NULL | Assessment decision |
| `reason_code` | VARCHAR(100) | NOT NULL | Decision rationale |
| `assessed_by_adjuster_id` | UUID | FK (User), NOT NULL | Adjuster who assessed |
| `assessed_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Assessment timestamp |
| `coverage_status` | ENUM | IN (FULL_COVERAGE, PARTIAL_COVERAGE, NO_COVERAGE), NOT NULL | Coverage determination |
| `coverage_reason_code` | VARCHAR(100) | nullable | Reason for coverage status |

**Indexes**
- (assessment_id): PRIMARY KEY
- (claim_id): UNIQUE, for assessment lookup
- (assessed_at): for historical queries

**Constraints**
- NOT NULL on all required fields
- assessed_amount >= 0
- payable_amount >= 0
- payable_amount <= assessed_amount (always after deductions)
- All fields IMMUTABLE after creation (database trigger + app logic)
- Foreign key: claim_id references Claim, UNIQUE constraint
- Foreign key: assessed_by_adjuster_id references User

**Relationships**
- Claim 1:1 Assessment (foreign key: claim_id)

**Example Record**
```json
{
  "assessment_id": "assess-uuid-1",
  "claim_id": "claim-uuid-1",
  "assessed_amount": 5000.00,
  "payable_amount": 4500.00,
  "deductible_applied": 300.00,
  "co_pay_applied": 200.00,
  "decision": "AUTO_APPROVE",
  "reason_code": "FULL_COVERAGE_APPROVED",
  "assessed_by_adjuster_id": "user-uuid-adj",
  "assessed_at": "2026-10-04T13:30:00Z",
  "coverage_status": "FULL_COVERAGE"
}
```

---

### FraudScreeningResult

Immutable fraud evaluation record.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `fraud_result_id` | UUID | PK, NOT NULL | Unique result identifier |
| `claim_id` | UUID | FK (Claim), NOT NULL | Associated claim |
| `rule_version_id` | UUID | FK (FraudRuleVersion), NOT NULL | Fraud rules used |
| `fraud_score` | NUMERIC(3,2) | NOT NULL, 0-1 | Fraud probability score |
| `fraud_rules_triggered` | JSONB | NOT NULL, default [] | Array of triggered rule names |
| `is_flagged` | BOOLEAN | NOT NULL | true if score >= threshold |
| `evaluated_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Evaluation timestamp |
| `evaluated_by_system` | BOOLEAN | NOT NULL, default true | true if automated |

**Indexes**
- (fraud_result_id): PRIMARY KEY
- (claim_id): for claim fraud results
- (is_flagged): for flagged claim queries
- (evaluated_at): for chronological queries

**Constraints**
- ALL FIELDS IMMUTABLE after creation
- fraud_score in range [0.0, 1.0]
- is_flagged is boolean
- Foreign key: claim_id, rule_version_id

**Relationships**
- Claim 1:N FraudScreeningResult (foreign key: claim_id)
- FraudRuleVersion 1:N FraudScreeningResult

---

### Settlement

Immutable payout ledger (WORM — Write-Once-Read-Many).

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `settlement_id` | UUID | PK, NOT NULL | Unique settlement identifier |
| `claim_id` | UUID | FK (Claim), NOT NULL | Associated claim |
| `payout_amount` | NUMERIC(10,2) | NOT NULL, >= 0, IMMUTABLE | Disbursed amount |
| `payout_state` | ENUM | IN (PENDING_DISBURSEMENT, DISBURSED, FAILED_RETRY), default PENDING_DISBURSEMENT | Payout status |
| `approved_by_admin_id` | UUID | FK (User), NOT NULL, IMMUTABLE | Admin who approved |
| `approved_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Approval timestamp |
| `disbursed_at` | TIMESTAMP | nullable, IMMUTABLE (once set) | When payout completed |
| `rejection_reason_code` | VARCHAR(100) | nullable | Reason if payout_state = FAILED_RETRY |

**Indexes**
- (settlement_id): PRIMARY KEY
- (claim_id): for settlement lookup by claim
- (approved_at): for chronological queries
- (payout_state): for status filtering

**Constraints**
- PRIMARY KEY, settlement_id
- NOT NULL on marked fields
- payout_amount >= 0
- IMMUTABLE: settlement_id, claim_id, payout_amount, approved_by_admin_id, approved_at
- disbursed_at cannot be changed once set (trigger enforces)
- NO DELETE: application and database constraints block deletion
- Foreign key: claim_id (UNIQUE: max 1 active settlement per claim, unless override)

**Relationships**
- Claim 1:N Settlement (foreign key: claim_id)

**Example Record**
```json
{
  "settlement_id": "settle-uuid-1",
  "claim_id": "claim-uuid-1",
  "payout_amount": 4500.00,
  "payout_state": "PENDING_DISBURSEMENT",
  "approved_by_admin_id": "admin-uuid-1",
  "approved_at": "2026-10-04T14:00:00Z",
  "disbursed_at": null
}
```

---

### SubClaim

Dispute or reopen request creating linked child claim.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `sub_claim_id` | UUID | PK, NOT NULL | Unique sub-claim identifier |
| `parent_claim_id` | UUID | FK (Claim), NOT NULL | Original settled claim |
| `related_claim_id` | UUID | FK (Claim), NOT NULL | Linked child claim (new FILED claim) |
| `sub_claim_type` | ENUM | IN (DISPUTE, REOPEN), NOT NULL | Dispute or reopen type |
| `reason` | TEXT | NOT NULL | Claimant reason for dispute |
| `created_by_customer_id` | UUID | FK (Customer), NOT NULL | Customer who filed dispute |
| `created_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Dispute filing timestamp |

**Indexes**
- (sub_claim_id): PRIMARY KEY
- (parent_claim_id): for linked claims query
- (related_claim_id): for child claim lookup
- (created_at): for chronological queries

**Constraints**
- NOT NULL on required fields
- All fields IMMUTABLE after creation
- Foreign keys: parent_claim_id, related_claim_id, created_by_customer_id
- parent_claim_id != related_claim_id

**Relationships**
- Claim 1:N SubClaim (foreign keys: parent_claim_id, related_claim_id)

---

### OverrideAuditLog

Immutable admin override decision audit trail.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `override_id` | UUID | PK, NOT NULL | Unique override identifier |
| `claim_id` | UUID | FK (Claim), NOT NULL, UNIQUE | Overridden claim |
| `override_type` | ENUM | IN (APPROVE_REJECTED, REJECT_APPROVED), NOT NULL | Type of override |
| `previous_state` | ENUM | IN (APPROVED, REJECTED), NOT NULL | State before override |
| `new_state` | ENUM | IN (APPROVED, REJECTED), NOT NULL | State after override |
| `reason_code` | VARCHAR(100) | NOT NULL | Override justification |
| `justification_comment` | TEXT | NOT NULL | Free-text explanation |
| `actor_id` | UUID | FK (User), NOT NULL, IMMUTABLE | Admin who overrode |
| `actor_email` | VARCHAR(255) | NOT NULL, IMMUTABLE | Admin email (audit trail) |
| `override_at` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Override timestamp |

**Indexes**
- (override_id): PRIMARY KEY
- (claim_id): UNIQUE, for override lookup
- (actor_id): for admin activity audit
- (override_at): for chronological queries

**Constraints**
- ALL FIELDS IMMUTABLE after creation (database trigger)
- NO DELETE operations allowed
- claim_id UNIQUE: max 1 override per claim
- previous_state != new_state
- Foreign key: claim_id

**Relationships**
- Claim 1:1 OverrideAuditLog (foreign key: claim_id, UNIQUE)

---

### AuditLog

Append-only audit trail for all material operations (WORM).

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `audit_id` | UUID | PK, NOT NULL | Unique audit entry identifier |
| `correlation_id` | UUID | NOT NULL | End-to-end tracing ID |
| `timestamp` | TIMESTAMP | NOT NULL, UTC, IMMUTABLE | Operation timestamp |
| `actor_id` | UUID | FK (User), NOT NULL, IMMUTABLE | User who performed operation |
| `actor_role` | ENUM | IN (ROLE_CUSTOMER, ROLE_ADJUSTER, ROLE_ADMIN), NOT NULL | User role |
| `operation_type` | ENUM | IN (CLAIM_CREATED, STATE_TRANSITION, DOCUMENT_UPLOADED, DOCUMENT_VERIFIED, FRAUD_EVALUATED, ASSESSMENT_SUBMITTED, SETTLEMENT_CONFIRMED, OVERRIDE_APPLIED), NOT NULL | Operation classification |
| `claim_id` | UUID | FK (Claim), NOT NULL | Affected claim |
| `previous_state` | ENUM | nullable | State before operation |
| `new_state` | ENUM | nullable | State after operation |
| `reason_code` | VARCHAR(100) | nullable | Operation reason |
| `detail_json` | JSONB | NOT NULL, default {} | Operation context (with PII redacted) |

**Indexes**
- (audit_id): PRIMARY KEY
- (claim_id): for claim audit history
- (actor_id): for user activity audit
- (timestamp): for time-range queries
- (operation_type): for operation filtering
- (correlation_id): for distributed tracing

**Constraints**
- ALL FIELDS IMMUTABLE after creation (database constraints)
- NO DELETE operations allowed
- timestamp in UTC
- Foreign key: claim_id
- detail_json contains `[REDACTED]` for PII fields

**Relationships**
- Claim 1:N AuditLog (foreign key: claim_id)

---

### FraudRuleVersion

Versioned fraud rule configuration (append-only).

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `rule_version_id` | UUID | PK, NOT NULL | Unique rule version identifier |
| `version_number` | INTEGER | NOT NULL | Version sequence |
| `line_of_business` | ENUM | IN (MOTOR, HEALTH, LIFE), NOT NULL | LOB these rules apply to |
| `is_active` | BOOLEAN | NOT NULL, default true | true if current active version |
| `fraud_threshold` | NUMERIC(3,2) | NOT NULL, 0-1 | Threshold score for flagging |
| `rules` | JSONB | NOT NULL | Array of rule definitions |
| `created_at` | TIMESTAMP | NOT NULL, UTC | Version creation timestamp |
| `created_by_admin_id` | UUID | FK (User), NOT NULL | Admin who created version |
| `effective_date` | DATE | NOT NULL | When rules became effective |

**Indexes**
- (rule_version_id): PRIMARY KEY
- (line_of_business, is_active): for current version lookup
- (version_number): for version history

**Constraints**
- NOT NULL on required fields
- fraud_threshold in range [0.0, 1.0]
- version_number monotonically increasing per LOB
- Foreign key: created_by_admin_id

**Relationships**
- User 1:N FraudRuleVersion (foreign key: created_by_admin_id)

**Example Record**
```json
{
  "rule_version_id": "rule-v1-uuid",
  "version_number": 1,
  "line_of_business": "MOTOR",
  "is_active": true,
  "fraud_threshold": 0.75,
  "rules": [
    {
      "rule_name": "claim_amount_outlier",
      "operator": "gt",
      "threshold": 50000,
      "weight": 40,
      "description": "Claim amount exceeds 50x policy average"
    },
    {
      "rule_name": "multiple_claims_same_period",
      "operator": "count_gt",
      "threshold": 3,
      "weight": 35,
      "description": "Customer filed >3 claims within 12 months"
    }
  ],
  "created_at": "2026-10-01T00:00:00Z",
  "created_by_admin_id": "admin-uuid-1",
  "effective_date": "2026-10-01"
}
```

---

### DocumentChecklist

Checklist configuration per line of business (read-only configuration).

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `checklist_id` | UUID | PK, NOT NULL | Unique checklist identifier |
| `line_of_business` | ENUM | IN (MOTOR, HEALTH, LIFE), NOT NULL | LOB these documents apply to |
| `required_documents` | JSONB | NOT NULL | Array of required document types |
| `version` | INTEGER | NOT NULL | Checklist version |
| `created_at` | TIMESTAMP | NOT NULL, UTC | Checklist creation |

**Example Record**
```json
{
  "checklist_id": "check-motor-uuid",
  "line_of_business": "MOTOR",
  "required_documents": [
    {
      "document_type": "POLICE_FIR",
      "required": true,
      "description": "Police First Information Report"
    },
    {
      "document_type": "REPAIR_INVOICE",
      "required": true,
      "description": "Repair shop invoice"
    }
  ],
  "version": 1,
  "created_at": "2026-10-01T00:00:00Z"
}
```

---

### User

User account and role management.

**Fields**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | UUID | PK, NOT NULL | Unique user identifier |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | User email address |
| `full_name` | VARCHAR(255) | NOT NULL | User display name |
| `role` | ENUM | IN (ROLE_CUSTOMER, ROLE_ADJUSTER, ROLE_ADMIN), NOT NULL | User role |
| `is_active` | BOOLEAN | NOT NULL, default true | Account active status |
| `created_at` | TIMESTAMP | NOT NULL, UTC | Account creation |
| `last_login_at` | TIMESTAMP | nullable | Last login timestamp |

**Indexes**
- (user_id): PRIMARY KEY
- (email): UNIQUE, for authentication
- (role): for role-based queries

---

## Financial Precision

All monetary fields use `NUMERIC(10,2)` for 2 decimal place precision (cents):
- claim_amount: 10,000.00
- payable_amount: 4,500.00
- deductible: 300.00

No floating-point types are used. Intermediate calculations preserve full precision until final rounding.

---

## Immutability Enforcement

**Database Level**
- IMMUTABLE fields use NOT NULL + database triggers to prevent UPDATE
- Triggers raise exceptions on UPDATE attempts for immutable fields
- DELETE operations blocked by foreign key constraints and explicit triggers

**Application Level**
- Repository layer enforces read-only methods for immutable records
- No UPDATE methods available for Settlement, OverrideAuditLog, AuditLog
- ImmutabilityViolationException raised on modification attempts

---

## Audit Trail Coverage

Every state transition triggers AuditLog entry:
- CLAIM_CREATED: when claim filed (E1-S2)
- STATE_TRANSITION: any state change (E1-S3, E2-S4, E4-S3, E5-S3)
- DOCUMENT_UPLOADED: when document uploaded (E2-S2)
- DOCUMENT_VERIFIED: when document verification completed (E2-S4)
- FRAUD_EVALUATED: when fraud score computed (E3-S3)
- ASSESSMENT_SUBMITTED: when assessment decision recorded (E4-S3)
- SETTLEMENT_CONFIRMED: when settlement created (E5-S3)
- OVERRIDE_APPLIED: when admin override executed (E7-S3)

---

## Summary

ClaimFlow data model enforces:
- **Immutability:** WORM (Write-Once-Read-Many) for settlements, audit trails, assessment records
- **Versioning:** Policy rules, fraud rules, checklists versioned for determinism
- **Determinism:** Rule versions pinned at intake for identical evaluation
- **Compliance:** Audit trail with PII redaction for SOX/GDPR
- **Financial Precision:** NUMERIC(10,2) for all monetary values
- **Relational Integrity:** Foreign keys, unique constraints, state machine validation
