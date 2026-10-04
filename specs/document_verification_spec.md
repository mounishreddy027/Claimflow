# Feature Specification: Document Verification & Checklist Enforcement
## Feature ID: SPEC-02 | Domain: Insurance Claims Operations (BC-AINE-005)

---

## 1. Feature Description & Scope

The **Document Verification & Checklist Enforcement** module enforces line-of-business specific documentary evidence requirements across Motor, Health, and Life claims. 

Before any filed claim can proceed to automated fraud screening, adjuster evaluation, or lifecycle transition to `UNDER_REVIEW`, this module verifies that all mandatory documents for that specific claim type have been uploaded and individually certified as `VERIFIED` by operations staff or verification workflows.

---

## 2. Acceptance Criteria

### AC-03: Document Checklist Enforcement by Claim Type
**Criterion Statement:** Document-checklist enforcement varies by claim type:
- **Motor:** Police FIR (`POLICE_FIR`) + Repair Invoice (`REPAIR_INVOICE`)
- **Health:** Hospital Bill (`HOSPITAL_BILL`) + Discharge Summary (`DISCHARGE_SUMMARY`)
- **Life:** Death Certificate (`DEATH_CERTIFICATE`)

- **Scenario 3.1: Complete Document Submission for Motor Claim**
  - **Given** a Motor claim in `FILED` status,
  - **When** both `POLICE_FIR` and `REPAIR_INVOICE` are uploaded and marked `VERIFIED`,
  - **Then** the claim's document verification status becomes `COMPLETE`,
  - **And** the claim is permitted to transition from `FILED` to `UNDER_REVIEW`.

- **Scenario 3.2: Missing Mandatory Document Blocks Motor Progression**
  - **Given** a Motor claim with only a `REPAIR_INVOICE` uploaded (missing `POLICE_FIR`),
  - **When** the system or assessor attempts to advance the claim to `UNDER_REVIEW`,
  - **Then** the transition is blocked,
  - **And** the system returns an error `INCOMPLETE_DOCUMENT_CHECKLIST` specifying missing item `POLICE_FIR`,
  - **And** the claim remains in `FILED` state.

- **Scenario 3.3: Health Claim Checklist Validation**
  - **Given** a Health claim in `FILED` status,
  - **When** both `HOSPITAL_BILL` and `DISCHARGE_SUMMARY` documents are verified,
  - **Then** the health document checklist is marked satisfied.

- **Scenario 3.4: Life Claim Checklist Validation**
  - **Given** a Life insurance claim in `FILED` status,
  - **When** the `DEATH_CERTIFICATE` is verified,
  - **Then** the life document checklist is marked satisfied.

- **Scenario 3.5: Document Rejection Workflow**
  - **Given** an uploaded document with illegible scan quality or mismatched claim details,
  - **When** the verification officer rejects the document with a mandatory reason code (e.g., `DOC_REJ_ILLEGIBLE` or `DOC_REJ_MISMATCH`),
  - **Then** the document status transitions to `REJECTED`,
  - **And** the claim checklist is marked `DEFICIENT`, preventing progression until a replacement document is uploaded.

---

## 3. Mandatory Checklist Matrix

| Claim Type | Document Code | Document Display Name | Mandatory / Optional | Validation Rule |
|---|---|---|---|---|
| **MOTOR** | `POLICE_FIR` | Police First Information Report | **Mandatory** | Valid FIR number; incident date matches claim incident date. |
| **MOTOR** | `REPAIR_INVOICE` | Auto Body Workshop Invoice | **Mandatory** | Itemized parts/labor breakdown; invoice total matches claim amount. |
| **HEALTH** | `HOSPITAL_BILL` | Itemized Hospital Final Bill | **Mandatory** | Hospital tax ID/registration; itemized pharmacy and room rent. |
| **HEALTH** | `DISCHARGE_SUMMARY` | Clinical Discharge Summary | **Mandatory** | Admission/discharge dates match billing duration; doctor signature. |
| **LIFE** | `DEATH_CERTIFICATE` | Certified Death Certificate | **Mandatory** | Government registrar seal/registration number; deceased matches policyholder. |

---

## 4. API Contract Specification

### 4.1 Endpoint: `GET /api/v1/claims/{claimId}/documents`
- **Response (`200 OK`):**
```json
{
  "claimId": "CLM-2026-00491",
  "claimType": "MOTOR",
  "checklistStatus": "INCOMPLETE",
  "mandatoryCount": 2,
  "verifiedCount": 1,
  "documents": [
    {
      "documentId": "DOC-901",
      "documentType": "POLICE_FIR",
      "fileName": "fir_copy_2026.pdf",
      "status": "VERIFIED",
      "verifiedAt": "2026-10-04T12:05:00Z",
      "verifiedBy": "assessor_user_1"
    },
    {
      "documentId": "DOC-902",
      "documentType": "REPAIR_INVOICE",
      "fileName": "auto_estimate.pdf",
      "status": "PENDING",
      "verifiedAt": null,
      "verifiedBy": null
    }
  ]
}
```

### 4.2 Endpoint: `POST /api/v1/claims/{claimId}/documents/{docId}/verify`
- **Request Body:**
```json
{
  "action": "VERIFY",
  "notes": "Police FIR registered under FIR# 2026/8812 verified legible"
}
```
- **Response (`200 OK`):**
```json
{
  "documentId": "DOC-901",
  "status": "VERIFIED",
  "verifiedBy": "assessor_user_1",
  "verifiedAt": "2026-10-04T12:05:00Z"
}
```

---

## 5. Non-Functional Criteria & Guardrails

- **NFR-03:** Document binary stubs and metadata containing claimant PII must not be written to logs.
- **NFR-04:** Document verification operations require authenticated role `ROLE_ASSESSOR` or `ROLE_ADMIN`.
- **NFR-08:** Checklist completeness must be strictly validated before allowing `ClaimStateMachine.transitionTo(UNDER_REVIEW)`.
