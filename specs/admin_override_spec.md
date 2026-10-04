# Feature Specification: Administrative Decision Override & Audit Logging
## Feature ID: SPEC-07 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Feature Description & Scope

The **Administrative Decision Override & Audit Logging** feature grants authorized claims supervisory personnel (`ROLE_ADMIN`) the ability to overturn automated or assessor adjudication decisions (`AUTO_APPROVE` or `REJECT`).

To preserve governance, prevent rogue reversals, and satisfy regulatory auditing standards, any override requires a mandatory justification comment and a valid policy reason code. The entire transaction is permanently recorded in an append-only audit trail logging the administrative actor's identity, the previous state, the new state, the reason code, and the exact UTC timestamp.

---

## 2. Acceptance Criteria

### AC-09: Audited Admin Decision Override
**Criterion Statement:** Admin can override an `AUTO_APPROVE` or `REJECT` decision with comment and reason code; the override action is audited with actor and timestamp.

- **Scenario 9.1: Admin Overrides Automated Rejection to Approved**
  - **Given** a claim `"CLM-2026-00491"` that was adjudicated as `REJECT` due to documentation technicality,
  - **When** an authenticated user with `ROLE_ADMIN` (`"admin_sarah"`) invokes the override endpoint with `newDecision = "APPROVED"`, `reasonCode = "ADM_OVR_EX_GRATIA_01"`, and `comment = "Executive approval granted per customer loyalty ex-gratia exception."`,
  - **Then** the claim's effective decision becomes `APPROVED`,
  - **And** the state transitions to `APPROVED`,
  - **And** an immutable audit record is appended in `claim_override_audits` capturing:
    - `claimId`: `"CLM-2026-00491"`
    - `actorId`: `"admin_sarah"`
    - `previousDecision`: `"REJECT"`
    - `newDecision`: `"APPROVED"`
    - `reasonCode`: `"ADM_OVR_EX_GRATIA_01"`
    - `comment`: `"Executive approval granted per customer loyalty ex-gratia exception."`
    - `timestamp`: `"2026-10-04T12:28:00Z"`
  - **And** HTTP `200 OK` is returned with the audit receipt.

- **Scenario 9.2: Admin Overrides Auto-Approve to Rejected (Fraud Suspected)**
  - **Given** a claim in `APPROVED` status that was auto-approved via STP,
  - **When** an admin discovers external evidence of collusion and submits an override to `REJECT` with reason code `"ADM_OVR_FRAUD_FLAG_02"` and explanatory comments,
  - **Then** the claim status is updated to `REJECTED`,
  - **And** any pending disbursement generation is blocked,
  - **And** the override action is audited with the admin's identity.

- **Scenario 9.3: Non-Admin Role Attempting Override (NFR-04 Violation)**
  - **Given** a user authenticated as `ROLE_ASSESSOR` or an unauthenticated client,
  - **When** they invoke `POST /api/v1/admin/claims/{claimId}/override`,
  - **Then** the controller security boundary intercepts the call,
  - **And** immediately returns HTTP `403 Forbidden`,
  - **And** no state or audit change occurs.

- **Scenario 9.4: Missing Justification Comment or Reason Code**
  - **Given** an admin invoking the override endpoint with an empty comment or missing reason code,
  - **When** the request is validated,
  - **Then** the controller rejects the request with HTTP `400 Bad Request`,
  - **And** an error message indicates `"Justification comment and reason code are mandatory for administrative overrides."`

---

## 3. API Contract Specification

### 3.1 Endpoint: `POST /api/v1/admin/claims/{claimId}/override`
- **Security:** Requires Bearer Token with `ROLE_ADMIN`
- **Request Headers:**
  - `Authorization: Bearer <ADMIN_JWT>`
  - `X-Correlation-ID: <UUID>`

- **Request Body Schema:**
```json
{
  "newDecision": "APPROVED",
  "reasonCode": "ADM_OVR_EX_GRATIA_01",
  "comment": "Executive approval granted per customer loyalty ex-gratia exception on review of secondary police testimony."
}
```

- **Response Body (`200 OK`):**
```json
{
  "overrideId": "OVR-2026-0091",
  "claimId": "CLM-2026-00491",
  "previousDecision": "REJECT",
  "newDecision": "APPROVED",
  "reasonCode": "ADM_OVR_EX_GRATIA_01",
  "comment": "Executive approval granted per customer loyalty ex-gratia exception on review of secondary police testimony.",
  "actorId": "admin_sarah",
  "timestamp": "2026-10-04T12:28:00Z"
}
```

---

## 4. Non-Functional Criteria & Guardrails

- **NFR-02:** Table `claim_override_audits` is strictly append-only.
- **NFR-03:** Comments are scrubbed of personal claimant identifiers if logged to system telemetry.
- **NFR-04:** Authentication and authority isolation verified via controller integration tests.
- **NFR-06:** Audit entry records request correlation ID for end-to-end tracing.
