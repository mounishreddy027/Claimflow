# Feature Specification: First Notice of Loss (FNOL) Intake
## Feature ID: SPEC-01 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Feature Description & Scope

The **First Notice of Loss (FNOL) Intake** feature provides the primary entry point for customers and policyholders to initiate an insurance claim across Horizon Insurance's three product lines: **Motor**, **Health**, and **Life**.

This module ingests the initial claim request, verifies the temporal coverage status of the policy on the date of the loss, validates required payload attributes, stubs supporting document storage, and initializes the claim lifecycle into the `FILED` state.

---

## 2. Acceptance Criteria

### AC-01: Customer FNOL Filing
**Criterion Statement:** Customer can file a First Notice of Loss (FNOL) with policy number, incident date, claim type (`MOTOR`, `HEALTH`, `LIFE`), and supporting documents (stubbed upload).

- **Scenario 1.1: Successful FNOL Submission for Motor Claim**
  - **Given** an existing policy `"POL-MTR-1001"` that is `ACTIVE` covering the incident date `"2026-09-15"`,
  - **When** the claimant submits a valid FNOL payload with `claimType = "MOTOR"`, `claimAmount = 3500.00`, incident details, and stubbed document attachments (`police_fir.pdf`, `repair_invoice.pdf`),
  - **Then** the platform creates a new claim record with a unique `claimId` (UUID format),
  - **And** the claim state is initialized strictly to `FILED`,
  - **And** HTTP status `201 Created` is returned with the claim tracking reference and document upload receipts.

- **Scenario 1.2: Successful FNOL Submission for Health and Life Claims**
  - **Given** an `ACTIVE` policy `"POL-HLT-2002"` or `"POL-LIF-3003"`,
  - **When** the claimant files an FNOL specifying `HEALTH` or `LIFE` with valid incident date and required document metadata,
  - **Then** the platform records the claim with status `FILED` and associates the documents in `PENDING` verification status.

- **Scenario 1.3: Validation of Mandatory Intake Fields**
  - **Given** an incoming intake request missing `policyNumber`, `incidentDate`, or `claimType`,
  - **When** the request hits the intake endpoint,
  - **Then** the system rejects the request with HTTP `400 Bad Request` and descriptive validation error messages.

---

### AC-02: Policy Status Enforcement on Incident Date
**Criterion Statement:** Claim is rejected with `PolicyNotActiveException` when the linked policy is not `ACTIVE` on the incident date.

- **Scenario 2.1: Incident Date Falls Outside Active Policy Effective Range**
  - **Given** policy `"POL-MTR-9999"` with effective coverage from `"2025-01-01"` to `"2025-12-31"`,
  - **When** a claimant files a claim reporting an incident date of `"2026-02-10"`,
  - **Then** the intake service determines the policy was `EXPIRED` on the incident date,
  - **And** immediately throws `PolicyNotActiveException`,
  - **And** returns HTTP `422 Unprocessable Entity` with error code `POLICY_NOT_ACTIVE_ON_INCIDENT_DATE`,
  - **And** no active claim record is persisted in the claims ledger.

- **Scenario 2.2: Policy in LAPSED, CANCELLED, or PENDING Status**
  - **Given** policy `"POL-HLT-5555"` marked with status `LAPSED` due to non-payment of premiums,
  - **When** an FNOL is submitted referencing `"POL-HLT-5555"`,
  - **Then** `PolicyNotActiveException` is raised,
  - **And** the intake operation halts without initiating document or fraud processing.

- **Scenario 2.3: Non-Existent Policy Number**
  - **Given** a policy number `"POL-NONEXISTENT"` not found in the policy registry,
  - **When** an FNOL is submitted,
  - **Then** the system returns HTTP `404 Not Found` with code `POLICY_NOT_FOUND`.

---

## 3. API Contract Specification

### 3.1 Endpoint: `POST /api/v1/claims/intake`
- **Request Headers:**
  - `Content-Type: application/json`
  - `X-Correlation-ID: <UUID>` (Optional; generated if absent)

- **Request Body Schema:**
```json
{
  "policyNumber": "POL-MTR-1001",
  "incidentDate": "2026-09-15",
  "claimType": "MOTOR",
  "claimAmount": 3500.00,
  "incidentDescription": "Front bumper collision at intersection",
  "supportingDocuments": [
    {
      "documentType": "POLICE_FIR",
      "fileName": "fir_copy_2026.pdf",
      "fileContentStub": "data:application/pdf;base64,stubbed_payload=="
    },
    {
      "documentType": "REPAIR_INVOICE",
      "fileName": "auto_body_estimate.pdf",
      "fileContentStub": "data:application/pdf;base64,stubbed_payload=="
    }
  ]
}
```

- **Successful Response (`201 Created`):**
```json
{
  "claimId": "CLM-2026-00491",
  "policyNumber": "POL-MTR-1001",
  "claimType": "MOTOR",
  "status": "FILED",
  "claimAmount": 3500.00,
  "incidentDate": "2026-09-15",
  "documentReceipts": [
    { "documentId": "DOC-901", "documentType": "POLICE_FIR", "status": "PENDING" },
    { "documentId": "DOC-902", "documentType": "REPAIR_INVOICE", "status": "PENDING" }
  ],
  "createdAt": "2026-10-04T12:00:00Z"
}
```

- **Failure Response (`422 Unprocessable Entity`):**
```json
{
  "error": "PolicyNotActiveException",
  "code": "POLICY_NOT_ACTIVE_ON_INCIDENT_DATE",
  "message": "Policy POL-MTR-9999 was not in ACTIVE status on incident date 2026-02-10 (Policy status: EXPIRED)",
  "policyNumber": "POL-MTR-9999",
  "incidentDate": "2026-02-10",
  "policyStatus": "EXPIRED",
  "timestamp": "2026-10-04T12:00:00Z"
}
```

---

## 4. Non-Functional Criteria & Guardrails

- **NFR-01:** `claimAmount` must be parsed as a 2-decimal fixed-point `BigDecimal`.
- **NFR-02:** Persisted claim intake rows are append-only.
- **NFR-03:** `incidentDescription` and document payloads are excluded from logs.
- **NFR-06:** Every intake transaction logs `correlation_id` and `claimId`.
