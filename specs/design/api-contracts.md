# API Contracts — ClaimFlow

Complete REST API specification with request/response schemas, status codes, and authentication requirements.

## Base URL

```
Development: http://localhost:8000/api
Production: https://api.claimflow.io/api
```

## Authentication

All endpoints require:
- Header `X-Actor-ID`: UUID of authenticated user
- Header `X-Actor-Role`: One of ROLE_CUSTOMER, ROLE_ADJUSTER, ROLE_ADMIN
- Request/Response Header `X-Correlation-ID`: UUID for end-to-end audit tracing

If missing, endpoint returns HTTP 401 Unauthorized.

## Rate Limiting

- 100 requests per minute per user (X-Actor-ID)
- Returns HTTP 429 Too Many Requests when exceeded
- Response includes `Retry-After` header

---

## E1: Claims Intake & Policy Validation

### POST /api/claims/intake

**Description:** File a new claim (FNOL). Creates claim in FILED state with policy validation.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_CUSTOMER
X-Correlation-ID: <uuid>
Content-Type: application/json
```

**Request Body**
```json
{
  "policy_number": "MOTOR-12345",
  "incident_date": "2026-10-04T10:00:00Z",
  "claim_type": "MOTOR|HEALTH|LIFE",
  "incident_description": "Vehicle collision on highway"
}
```

**Response — HTTP 201 Created**
```json
{
  "claim_id": "claim-uuid",
  "policy_id": "policy-uuid",
  "claim_state": "FILED",
  "created_at": "2026-10-04T10:30:00Z",
  "policy_rule_version_id": "rule-v1-uuid",
  "incident_date": "2026-10-04T10:00:00Z",
  "claim_type": "MOTOR"
}
```

**Response Headers**
```
X-Correlation-ID: <uuid>
```

**Error Responses**

HTTP 404 Not Found
```json
{
  "error_code": "POLICY_NOT_FOUND",
  "message": "Policy number MOTOR-12345 not found",
  "correlation_id": "<uuid>"
}
```

HTTP 422 Unprocessable Entity
```json
{
  "error_code": "POLICY_NOT_ACTIVE",
  "reason_code": "POLICY_EXPIRED|POLICY_NOT_EFFECTIVE",
  "message": "Policy expired on 2026-09-01, incident date is 2026-10-04",
  "policy_number": "MOTOR-12345",
  "incident_date": "2026-10-04T10:00:00Z",
  "policy_effective_date": "2025-01-01T00:00:00Z",
  "policy_expiry_date": "2026-09-01T00:00:00Z",
  "correlation_id": "<uuid>"
}
```

HTTP 400 Bad Request
```json
{
  "error_code": "INVALID_CLAIM_TYPE",
  "message": "Claim type must be one of: MOTOR, HEALTH, LIFE",
  "correlation_id": "<uuid>"
}
```

---

### GET /api/claims/{claim_id}

**Description:** Query claim status. Returns current state, reason codes, missing documents, and payable amount based on role.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_CUSTOMER|ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "claim_state": "UNDER_REVIEW",
  "incident_date": "2026-10-04T10:00:00Z",
  "policy_number": "MOTOR-12345",
  "line_of_business": "MOTOR",
  "created_at": "2026-10-04T10:30:00Z",
  "reason_code": null,
  "missing_documents": ["POLICE_FIR", "REPAIR_INVOICE"],
  "payable_amount": null,
  "rejection_reason_code": null,
  "incident_description": "[REDACTED]"
}
```

**Response — HTTP 200 OK (Adjuster/Admin view, full details)**
```json
{
  "claim_id": "claim-uuid",
  "claim_state": "UNDER_REVIEW",
  "incident_date": "2026-10-04T10:00:00Z",
  "policy_number": "MOTOR-12345",
  "line_of_business": "MOTOR",
  "created_at": "2026-10-04T10:30:00Z",
  "reason_code": "DOCS_VERIFIED",
  "missing_documents": [],
  "payable_amount": null,
  "rejection_reason_code": null,
  "incident_description": "Vehicle collision on highway near highway exit 42",
  "fraud_score": 0.35,
  "fraud_flagged": false,
  "assessment_status": null
}
```

**Error Response — HTTP 404 Not Found**
```json
{
  "error_code": "CLAIM_NOT_FOUND",
  "message": "Claim claim-uuid not found",
  "correlation_id": "<uuid>"
}
```

---

## E2: Document Management & Verification

### POST /api/claims/{claim_id}/documents

**Description:** Upload supporting document. Returns document ID and metadata.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_CUSTOMER|ROLE_ADJUSTER
X-Correlation-ID: <uuid>
Content-Type: multipart/form-data
```

**Request Body (multipart)**
```
file: <binary blob, max 10MB>
document_type: POLICE_FIR|REPAIR_INVOICE|HOSPITAL_BILL|DISCHARGE_SUMMARY|DEATH_CERTIFICATE
```

**Response — HTTP 201 Created**
```json
{
  "document_id": "doc-uuid",
  "claim_id": "claim-uuid",
  "file_name": "police_report.pdf",
  "document_type": "POLICE_FIR",
  "file_url": "/files/claim-uuid/doc-uuid/police_report.pdf",
  "uploaded_at": "2026-10-04T11:00:00Z",
  "status": "PENDING_VERIFICATION",
  "file_size_bytes": 524288
}
```

**Error Response — HTTP 400 Bad Request**
```json
{
  "error_code": "INVALID_DOCUMENT_TYPE",
  "message": "Document type must be one of: POLICE_FIR, REPAIR_INVOICE, HOSPITAL_BILL, DISCHARGE_SUMMARY, DEATH_CERTIFICATE",
  "correlation_id": "<uuid>"
}
```

**Error Response — HTTP 404 Not Found**
```json
{
  "error_code": "CLAIM_NOT_FOUND",
  "message": "Claim claim-uuid not found",
  "correlation_id": "<uuid>"
}
```

---

### GET /api/document-verification-queue

**Description:** Retrieve pending document verification queue. Adjuster view only.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
```

**Query Parameters**
```
page: integer, default 1
limit: integer, default 20, max 100
```

**Response — HTTP 200 OK**
```json
{
  "total_count": 42,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "items": [
    {
      "claim_id": "claim-uuid-1",
      "policy_number": "MOTOR-12345",
      "line_of_business": "MOTOR",
      "created_at": "2026-10-04T10:30:00Z",
      "uploaded_documents": [
        {
          "document_id": "doc-uuid-1",
          "document_type": "POLICE_FIR",
          "status": "PENDING_VERIFICATION",
          "uploaded_at": "2026-10-04T11:00:00Z"
        }
      ],
      "missing_documents": ["REPAIR_INVOICE"]
    }
  ]
}
```

---

### POST /api/claims/{claim_id}/verify-documents

**Description:** Submit document verification decisions. Transitions claim to UNDER_REVIEW if all required docs verified.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
Content-Type: application/json
```

**Request Body**
```json
{
  "decisions": [
    {
      "document_id": "doc-uuid-1",
      "status": "VERIFIED|REJECTED",
      "reason_code": "ACCEPTABLE|UNREADABLE|INVALID_FORMAT"
    },
    {
      "document_id": "doc-uuid-2",
      "status": "VERIFIED",
      "reason_code": "ACCEPTABLE"
    }
  ],
  "verified_by_adjuster_id": "adjuster-uuid"
}
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "claim_state": "UNDER_REVIEW",
  "reason_code": "DOCS_VERIFIED",
  "verification_results": [
    {
      "document_id": "doc-uuid-1",
      "status": "VERIFIED",
      "verified_at": "2026-10-04T12:00:00Z"
    },
    {
      "document_id": "doc-uuid-2",
      "status": "VERIFIED",
      "verified_at": "2026-10-04T12:00:00Z"
    }
  ]
}
```

**Error Response — HTTP 422 Unprocessable Entity**
```json
{
  "error_code": "INCOMPLETE_DOCUMENT_SET",
  "message": "Required document type REPAIR_INVOICE not verified",
  "missing_documents": ["REPAIR_INVOICE"],
  "correlation_id": "<uuid>"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "INVALID_CLAIM_STATE",
  "message": "Claim must be in FILED state, current state is UNDER_REVIEW",
  "correlation_id": "<uuid>"
}
```

---

## E3: Fraud Detection & Scoring

### POST /api/claims/{claim_id}/evaluate-fraud

**Description:** Evaluate claim against fraud rules. Records fraud score immutably.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
```

**Request Body**
```json
{}
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "fraud_score": 0.45,
  "fraud_rules_triggered": ["claim_amount_outlier", "multiple_claims_same_period"],
  "is_flagged": true,
  "claim_state": "UNDER_REVIEW",
  "internal_status": "FLAGGED_FOR_FRAUD_REVIEW",
  "evaluated_at": "2026-10-04T13:00:00Z"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "INVALID_CLAIM_STATE",
  "message": "Claim must be in UNDER_REVIEW state, current state is FILED",
  "correlation_id": "<uuid>"
}
```

**Error Response — HTTP 500 Internal Server Error**
```json
{
  "error_code": "FRAUD_RULES_NOT_AVAILABLE",
  "message": "Fraud rule version not found for rule_id: rule-v1-uuid",
  "correlation_id": "<uuid>"
}
```

---

## E4: Assessment & Adjudication

### POST /api/claims/{claim_id}/assess

**Description:** Submit assessment decision. Triggers payout calculation. Transitions claim state.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
Content-Type: application/json
```

**Request Body**
```json
{
  "decision": "AUTO_APPROVE|MANUAL_REVIEW|REJECT",
  "reason_code": "FULL_COVERAGE_APPROVED|FRAUD_THRESHOLD_EXCEEDED|COVERAGE_EXCLUDED",
  "assessed_by_adjuster_id": "adjuster-uuid"
}
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "assessment_id": "assessment-uuid",
  "decision": "AUTO_APPROVE",
  "claim_state": "APPROVED",
  "assessed_amount": 5000.00,
  "payable_amount": 4500.00,
  "deductible_applied": 300.00,
  "co_pay_applied": 200.00,
  "reason_code": "FULL_COVERAGE_APPROVED",
  "assessed_at": "2026-10-04T13:30:00Z"
}
```

**Response — HTTP 200 OK (Manual Review)**
```json
{
  "claim_id": "claim-uuid",
  "assessment_id": "assessment-uuid",
  "decision": "MANUAL_REVIEW",
  "claim_state": "UNDER_REVIEW",
  "internal_status": "ESCALATED_REVIEW",
  "assessed_at": "2026-10-04T13:30:00Z"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "INVALID_CLAIM_STATE",
  "message": "Claim must be in UNDER_REVIEW state, current state is FILED",
  "correlation_id": "<uuid>"
}
```

---

## E5: Settlement & Immutable Payouts

### POST /api/claims/{claim_id}/settle

**Description:** Confirm settlement. Triggers immutable payout ledger recording. Transitions claim to SETTLED.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADMIN
X-Correlation-ID: <uuid>
Content-Type: application/json
```

**Request Body**
```json
{
  "approved_by_admin_id": "admin-uuid",
  "settlement_notes": "Approved for payment"
}
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "settlement_id": "settlement-uuid",
  "payout_amount": 4500.00,
  "payout_state": "PENDING_DISBURSEMENT",
  "approved_at": "2026-10-04T14:00:00Z",
  "claim_state": "SETTLED",
  "reason_code": "SETTLEMENT_CONFIRMED"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "INVALID_CLAIM_STATE",
  "message": "Claim must be in APPROVED state, current state is UNDER_REVIEW",
  "correlation_id": "<uuid>"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "SETTLEMENT_ALREADY_EXISTS",
  "message": "Settlement already recorded for claim",
  "settlement_id": "settlement-uuid",
  "correlation_id": "<uuid>"
}
```

---

## E6: Dispute & Sub-Claim Management

### POST /api/claims/{claim_id}/dispute

**Description:** File a dispute or reopen request on settled claim. Creates linked sub-claim.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_CUSTOMER|ROLE_ADJUSTER
X-Correlation-ID: <uuid>
Content-Type: application/json
```

**Request Body**
```json
{
  "sub_claim_type": "DISPUTE|REOPEN",
  "reason": "Payout amount is insufficient; additional damage discovered",
  "created_by_customer_id": "customer-uuid"
}
```

**Response — HTTP 201 Created**
```json
{
  "sub_claim_id": "subclaim-uuid",
  "parent_claim_id": "parent-claim-uuid",
  "child_claim_id": "child-claim-uuid",
  "sub_claim_type": "DISPUTE",
  "created_at": "2026-10-04T15:00:00Z"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "INVALID_CLAIM_STATE",
  "message": "Parent claim must be in SETTLED state, current state is APPROVED",
  "correlation_id": "<uuid>"
}
```

---

### GET /api/claims/{claim_id}/linked-claims

**Description:** Retrieve parent claim and all linked sub-claims. Shows parent status (REOPENED if disputes exist).

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_CUSTOMER|ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
```

**Response — HTTP 200 OK**
```json
{
  "parent_claim": {
    "claim_id": "parent-claim-uuid",
    "claim_state": "SETTLED",
    "status": "REOPENED",
    "created_at": "2026-10-04T10:30:00Z",
    "settled_at": "2026-10-04T14:00:00Z"
  },
  "sub_claims": [
    {
      "sub_claim_id": "subclaim-uuid",
      "child_claim_id": "child-claim-uuid",
      "sub_claim_type": "DISPUTE",
      "created_at": "2026-10-04T15:00:00Z",
      "child_claim_state": "FILED"
    }
  ]
}
```

---

## E7: Admin, Audit & Compliance

### POST /api/claims/{claim_id}/override-decision

**Description:** Admin override of assessment decision. Rare operation, creates immutable override audit log.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADMIN
X-Correlation-ID: <uuid>
Content-Type: application/json
```

**Request Body**
```json
{
  "override_decision": "APPROVE_REJECTED|REJECT_APPROVED",
  "reason_code": "LEGITIMATE_HIGH_VALUE|CLERICAL_ERROR|FRAUD_UNRELATED",
  "justification_comment": "Claimant provided additional evidence of legitimate claim",
  "admin_actor_id": "admin-uuid"
}
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "override_id": "override-uuid",
  "override_decision": "APPROVE_REJECTED",
  "previous_state": "REJECTED",
  "new_state": "APPROVED",
  "settlement_id": "settlement-uuid",
  "payout_amount": 4500.00,
  "override_at": "2026-10-04T16:00:00Z"
}
```

**Error Response — HTTP 403 Forbidden**
```json
{
  "error_code": "ADMIN_ROLE_REQUIRED",
  "message": "User must have ROLE_ADMIN to override decisions",
  "correlation_id": "<uuid>"
}
```

**Error Response — HTTP 409 Conflict**
```json
{
  "error_code": "CLAIM_ALREADY_OVERRIDDEN",
  "message": "Claim has already been overridden; maximum one override per claim",
  "override_id": "override-uuid",
  "correlation_id": "<uuid>"
}
```

---

### GET /api/audit-trail/{claim_id}

**Description:** Retrieve complete immutable audit history for a claim.

**Request Headers**
```
X-Actor-ID: <uuid>
X-Actor-Role: ROLE_ADJUSTER|ROLE_ADMIN
X-Correlation-ID: <uuid>
```

**Query Parameters**
```
page: integer, default 1
limit: integer, default 50, max 200
operation_type: optional filter (CLAIM_CREATED, STATE_TRANSITION, etc.)
timestamp_from: optional ISO 8601 start date
timestamp_to: optional ISO 8601 end date
```

**Response — HTTP 200 OK**
```json
{
  "claim_id": "claim-uuid",
  "total_count": 15,
  "page": 1,
  "limit": 50,
  "has_next": false,
  "audit_entries": [
    {
      "audit_id": "audit-uuid-1",
      "correlation_id": "correlation-uuid",
      "timestamp": "2026-10-04T10:30:00Z",
      "actor_id": "customer-uuid",
      "actor_role": "ROLE_CUSTOMER",
      "operation_type": "CLAIM_CREATED",
      "claim_id": "claim-uuid",
      "previous_state": null,
      "new_state": "FILED",
      "reason_code": null,
      "detail_json": {
        "policy_number": "MOTOR-12345",
        "incident_date": "2026-10-04T10:00:00Z",
        "claim_type": "MOTOR"
      }
    },
    {
      "audit_id": "audit-uuid-2",
      "correlation_id": "correlation-uuid",
      "timestamp": "2026-10-04T12:00:00Z",
      "actor_id": "adjuster-uuid",
      "actor_role": "ROLE_ADJUSTER",
      "operation_type": "DOCUMENT_VERIFIED",
      "claim_id": "claim-uuid",
      "previous_state": "FILED",
      "new_state": "UNDER_REVIEW",
      "reason_code": "DOCS_VERIFIED",
      "detail_json": {
        "documents_verified": 2,
        "document_types": ["POLICE_FIR", "REPAIR_INVOICE"]
      }
    }
  ]
}
```

**Error Response — HTTP 404 Not Found**
```json
{
  "error_code": "CLAIM_NOT_FOUND",
  "message": "Claim claim-uuid not found",
  "correlation_id": "<uuid>"
}
```

---

## Common Error Codes

| Code | Meaning | HTTP Status |
|------|---------|------------|
| `POLICY_NOT_FOUND` | Policy number does not exist | 404 |
| `POLICY_NOT_ACTIVE` | Policy not active on incident date | 422 |
| `CLAIM_NOT_FOUND` | Claim ID does not exist | 404 |
| `INVALID_CLAIM_STATE` | Claim not in expected state for operation | 409 |
| `INVALID_DOCUMENT_TYPE` | Document type not in enum | 400 |
| `INCOMPLETE_DOCUMENT_SET` | Required documents not verified | 422 |
| `FRAUD_RULES_NOT_AVAILABLE` | Fraud rule version not found | 500 |
| `ADMIN_ROLE_REQUIRED` | Operation requires ROLE_ADMIN | 403 |
| `CLAIM_ALREADY_OVERRIDDEN` | Claim already has one override | 409 |
| `SETTLEMENT_ALREADY_EXISTS` | Settlement already recorded | 409 |
| `MISSING_CORRELATION_ID` | X-Correlation-ID header missing | 400 |
| `MISSING_ACTOR_ID` | X-Actor-ID header missing | 401 |
| `MISSING_ACTOR_ROLE` | X-Actor-Role header missing | 401 |

---

## Pagination

All list endpoints support pagination with:
- `page`: 1-indexed page number (default 1)
- `limit`: items per page, 1-1000 (defaults and max vary by endpoint)
- Response includes `total_count`, `has_next`, `page`, `limit`

---

## Correlation ID Tracing

Every request/response includes `X-Correlation-ID` header for end-to-end audit tracing. If client does not provide one, server generates a new UUID. All related operations (e.g., settlement confirmation + subsequent audit entries) share the same correlation ID.

---

## Summary

ClaimFlow API follows REST conventions with:
- Clear separation of concerns (intake, documents, fraud, assessment, settlement, disputes, audit)
- Immutable operations (no PUT/PATCH for settlement or audit records)
- Role-based access control (ROLE_CUSTOMER, ROLE_ADJUSTER, ROLE_ADMIN)
- Comprehensive error handling with machine-readable error codes
- Request/response correlation for audit and debugging
