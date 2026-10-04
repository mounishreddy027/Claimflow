# Component Map — ClaimFlow

Story-to-file mapping showing which files are created or modified to implement each acceptance criterion.

## Group A — Foundation Layer (No Dependencies)

### E1-S1: Policy Active Date Validation

Implements policy active date rule (AC-01, AC-02, AC-03, AC-04, AC-05).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/types/exceptions.py` | PolicyNotActiveException, reason codes |
| `backend/src/claimflow/services/policy_service.py` | PolicyService.validate_policy_active() |
| `backend/tests/unit/test_policy_service.py` | Unit tests for policy validation |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/types/enums.py` | Add PolicyReasonCode enum (POLICY_EXPIRED, POLICY_NOT_EFFECTIVE) |
| `backend/src/claimflow/database/models.py` | Add Policy model with effective_date, expiry_date fields |

---

### E2-S1: Document Checklist Definition Per LOB

Implements document checklist configuration (AC-01, AC-02, AC-03, AC-04, AC-05).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/config_loaders/document_checklist_loader.py` | Load checklists from JSON config |
| `backend/src/claimflow/database/seed_data/checklists.json` | Checklist configuration: Motor, Health, Life |
| `backend/tests/unit/test_document_checklist_loader.py` | Unit tests for checklist loading |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/types/enums.py` | Add DocumentType enum (POLICE_FIR, REPAIR_INVOICE, etc.) |
| `backend/src/claimflow/database/models.py` | Add DocumentChecklist model |

---

### E3-S2: Fraud Threshold Configuration Loader

Implements fraud rule version configuration (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/config_loaders/fraud_rules_loader.py` | Load fraud rules and versions from JSON |
| `backend/src/claimflow/database/seed_data/fraud_rules.json` | Fraud rule definitions per LOB |
| `backend/tests/unit/test_fraud_rules_loader.py` | Unit tests for fraud rule loading |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add FraudRuleVersion model with versioning |
| `backend/src/claimflow/config.py` | Load fraud rules at startup |

---

### E4-S1: Coverage Assessment Logic

Implements coverage assessment service (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/services/assessment_service.py` | AssessmentService.evaluate_coverage() |
| `backend/tests/unit/test_assessment_service.py` | Unit tests for coverage assessment |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/types/enums.py` | Add CoverageStatus enum (FULL_COVERAGE, PARTIAL_COVERAGE, NO_COVERAGE) |

---

### E7-S2: Audit Trail Recording & Immutability Enforcement

Implements audit trail system (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/repositories/audit_repository.py` | AuditRepository (append-only, immutable) |
| `backend/src/claimflow/services/audit_service.py` | Record audit entries with PII redaction |
| `backend/src/claimflow/utils/pii_redaction.py` | PII redaction helpers |
| `backend/tests/unit/test_audit_service.py` | Unit tests for audit trail |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add AuditLog model with immutability constraints |
| `backend/src/claimflow/types/enums.py` | Add OperationType enum (CLAIM_CREATED, STATE_TRANSITION, etc.) |
| `backend/src/claimflow/database/migrations/versions/` | Migration: immutability triggers on AuditLog |

---

## Group B — Early Service & Persistence Layer

### E1-S2: Claim Intake Endpoint (FNOL Filing)

Implements claim intake API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/claims.py` | POST /api/claims/intake endpoint |
| `backend/src/claimflow/repositories/claim_repository.py` | ClaimRepository.create_claim() |
| `backend/tests/integration/test_claim_intake_flow.py` | Integration test for intake flow |
| `frontend/src/pages/ClaimIntakePage.tsx` | FNOL filing form UI |
| `frontend/src/api/claims.ts` | Client method: submitClaim() |
| `frontend/tests/e2e/claim-intake.spec.ts` | E2E test for intake UI |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add Claim model with state machine |
| `backend/src/claimflow/api/middleware.py` | Add correlation ID middleware |
| `backend/src/claimflow/types/enums.py` | Add ClaimState, ClaimType enums |
| `backend/src/claimflow/api/schemas.py` | Add ClaimIntakeRequest, ClaimResponse schemas |

---

### E3-S1: Deterministic Fraud Rule Engine

Implements fraud scoring engine (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/services/fraud_service.py` | FraudService.evaluate_claim_fraud() |
| `backend/tests/unit/test_fraud_service.py` | Unit tests for fraud engine |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/types/enums.py` | Add fraud scoring constants |

---

### E4-S2: Payout Calculation with Financial Invariants

Implements payout calculation (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/services/payout_service.py` | PayoutService.calculate_payout() |
| `backend/src/claimflow/utils/financial.py` | Fixed-point arithmetic helpers |
| `backend/tests/unit/test_payout_service.py` | Unit tests for payout calculation |

---

### E5-S1: Immutable Payout Ledger Repository

Implements WORM settlement ledger (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/repositories/settlement_repository.py` | SettlementRepository (WORM enforcement) |
| `backend/src/claimflow/utils/immutability.py` | Immutability constraint helpers |
| `backend/tests/unit/test_settlement_repository.py` | Unit tests for immutability |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add Settlement model with immutability |
| `backend/src/claimflow/database/migrations/versions/` | Migration: WORM constraints on Settlement |

---

## Group C — Mid-Pipeline API & Service Layer

### E1-S3: Claim Status Query Endpoint

Implements claim status API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `frontend/src/pages/ClaimStatusPage.tsx` | Claim status query UI |
| `frontend/src/api/claims.ts` | Client method: getClaimStatus() |
| `frontend/src/components/claim/ClaimSummary.tsx` | Claim details display component |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/api/routes/claims.py` | GET /api/claims/{claim_id} endpoint |
| `backend/src/claimflow/repositories/claim_repository.py` | Add get_claim() query method |
| `backend/src/claimflow/api/middleware.py` | Add role-based access control |
| `backend/src/claimflow/api/schemas.py` | Add ClaimDetailResponse schema |

---

### E2-S2: Document Upload & Storage Endpoint

Implements document upload API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/documents.py` | POST /api/claims/{id}/documents endpoint |
| `backend/tests/integration/test_document_workflow.py` | Integration tests for document flow |
| `frontend/src/pages/DocumentUploadPage.tsx` | Document upload UI |
| `frontend/src/components/document/DocumentUploader.tsx` | Multi-file upload component |
| `frontend/src/api/documents.ts` | Client method: uploadDocument() |
| `frontend/tests/e2e/document-upload.spec.ts` | E2E test for document upload |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add Document model |
| `backend/src/claimflow/repositories/document_repository.py` | Add document CRUD + immutability |
| `backend/src/claimflow/api/schemas.py` | Add DocumentUploadRequest, DocumentResponse |

---

### E3-S3: Fraud Screening & Routing Endpoint

Implements fraud evaluation API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/fraud.py` | POST /api/claims/{id}/evaluate-fraud endpoint |
| `backend/src/claimflow/repositories/fraud_repository.py` | FraudScreeningResult recording |
| `backend/tests/integration/test_fraud_assessment_flow.py` | Integration tests for fraud eval |
| `frontend/src/pages/FraudScreeningPage.tsx` | Fraud evaluation UI (adjuster view) |
| `frontend/src/components/assessment/FraudScoreDisplay.tsx` | Fraud score visualization |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add FraudScreeningResult model |
| `backend/src/claimflow/api/schemas.py` | Add FraudEvaluationResponse schema |

---

### E4-S3: Assessment Decision Submission Endpoint

Implements assessment API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/assessment.py` | POST /api/claims/{id}/assess endpoint |
| `backend/src/claimflow/repositories/assessment_repository.py` | Assessment immutable recording |
| `backend/tests/integration/test_assessment_flow.py` | Integration test for assessment |
| `frontend/src/pages/AssessmentPage.tsx` | Assessment decision UI (adjuster view) |
| `frontend/src/components/assessment/AssessmentDetails.tsx` | Assessment result display |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add Assessment model with immutability |
| `backend/src/claimflow/api/schemas.py` | Add AssessmentRequest, AssessmentResponse |
| `backend/src/claimflow/repositories/claim_repository.py` | Update state transitions |

---

### E5-S2: Settlement Payout Generation Service

Implements settlement generation service (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/services/settlement_service.py` | SettlementService.generate_settlement() |
| `backend/tests/unit/test_settlement_service.py` | Unit tests for settlement generation |

---

## Group D — Document Verification & Settlement Finalization

### E2-S3: Document Verification Queue Service

Implements verification queue API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `frontend/src/pages/VerificationQueuePage.tsx` | Verification queue UI (adjuster view) |
| `frontend/src/components/document/DocumentList.tsx` | Document list for queue |
| `frontend/src/api/documents.ts` | Client method: getVerificationQueue() |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/api/routes/documents.py` | GET /api/document-verification-queue endpoint |
| `backend/src/claimflow/repositories/document_repository.py` | Add queue query method |

---

### E2-S4: Verification Decision Submission Endpoint

Implements verification decision API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/verification.py` | POST /api/claims/{id}/verify-documents endpoint |
| `frontend/src/pages/VerificationDecisionPage.tsx` | Verification decision UI |
| `frontend/src/components/document/DocumentVerifier.tsx` | Document verification decision component |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/repositories/document_repository.py` | Update verification status |
| `backend/src/claimflow/repositories/claim_repository.py` | State transition: FILED → UNDER_REVIEW |
| `backend/src/claimflow/api/schemas.py` | Add VerifyDocumentsRequest, VerificationResultResponse |

---

### E5-S3: Settlement Confirmation & Ledger Recording Endpoint

Implements settlement confirmation API (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/settlement.py` | POST /api/claims/{id}/settle endpoint |
| `backend/tests/integration/test_settlement_flow.py` | Integration test for settlement flow |
| `frontend/src/pages/SettlementPage.tsx` | Settlement confirmation UI (admin view) |
| `frontend/src/components/assessment/PayoutCalculator.tsx` | Payout display component |
| `frontend/src/api/settlement.ts` | Client method: confirmSettlement() |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/repositories/settlement_repository.py` | Create settlement with immutability |
| `backend/src/claimflow/api/schemas.py` | Add SettlementRequest, SettlementResponse |

---

### E6-S1: Dispute Intake & Sub-Claim Generation

Implements dispute creation service (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/services/dispute_service.py` | DisputeService.create_dispute() |
| `backend/src/claimflow/repositories/subclaim_repository.py` | SubClaim and child claim creation |
| `backend/tests/integration/test_dispute_flow.py` | Integration test for dispute flow |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add SubClaim model |

---

## Group E — Dispute Handling & Admin Overrides

### E6-S2: Parent Claim State Management for Reopened Claims

Implements parent claim reopened status (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06).

**Files Created**
| File | Purpose |
|------|---------|
| `frontend/src/pages/DisputePage.tsx` | Dispute filing UI |
| `frontend/src/api/disputes.ts` | Client method: fileDispute(), getLinkedClaims() |
| `frontend/src/components/claim/ClaimTimeline.tsx` | Claim state and sub-claims timeline |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/api/routes/disputes.py` | POST /api/claims/{id}/dispute, GET /api/claims/{id}/linked-claims |
| `backend/src/claimflow/repositories/claim_repository.py` | Update status flag to REOPENED |
| `backend/src/claimflow/api/schemas.py` | Add DisputeRequest, DisputeResponse, LinkedClaimsResponse |

---

### E7-S1: Decision Override Authority & Implementation

Implements admin override service (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/services/override_service.py` | OverrideService.override_decision() |
| `backend/src/claimflow/repositories/override_repository.py` | OverrideAuditLog (immutable) |
| `backend/tests/unit/test_override_service.py` | Unit tests for override |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/database/models.py` | Add OverrideAuditLog model with immutability |

---

### E7-S3: Admin Override Decision Endpoint

Implements override endpoint (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08).

**Files Created**
| File | Purpose |
|------|---------|
| `backend/src/claimflow/api/routes/overrides.py` | POST /api/claims/{id}/override-decision endpoint |
| `backend/tests/integration/test_override_flow.py` | Integration test for override flow |
| `frontend/src/pages/OverridePage.tsx` | Admin override UI |
| `frontend/src/api/overrides.ts` | Client method: overrideDecision() |

**Files Modified**
| File | Changes |
|------|---------|
| `backend/src/claimflow/api/schemas.py` | Add OverrideRequest, OverrideResponse |

---

## Cross-Cutting: Audit Trail

### E7-S2: Audit Trail Recording & Immutability Enforcement (Triggered by All State Transitions)

Every state transition in the following endpoints triggers an AuditLog entry:

**E1-S2**: Claim intake → CLAIM_CREATED
**E2-S4**: Document verification → STATE_TRANSITION (FILED → UNDER_REVIEW)
**E3-S3**: Fraud evaluation → FRAUD_EVALUATED
**E4-S3**: Assessment decision → ASSESSMENT_SUBMITTED
**E5-S3**: Settlement confirmation → SETTLEMENT_CONFIRMED
**E6-S1**: Dispute creation → STATE_TRANSITION (parent flag change)
**E7-S3**: Admin override → OVERRIDE_APPLIED

Also implemented:

**Files Modified**
| File | Changes |
|------|---------|
| All route files | Call AuditService.record_audit_entry() after state changes |
| `backend/src/claimflow/repositories/claim_repository.py` | Trigger AuditLog on every state transition |
| `frontend/src/pages/` | All pages link to audit trail viewing |
| `frontend/src/pages/AuditTrailPage.tsx` | GET /api/audit-trail/{claim_id} UI |
| `frontend/src/api/audit.ts` | Client method: getAuditTrail() |

---

## Frontend Pages Summary

| Page | Story | Purpose |
|------|-------|---------|
| `ClaimIntakePage` | E1-S2 | File new claim (FNOL) |
| `ClaimStatusPage` | E1-S3 | Query claim status |
| `DocumentUploadPage` | E2-S2 | Upload supporting documents |
| `VerificationQueuePage` | E2-S3 | View document verification queue (adjuster) |
| `VerificationDecisionPage` | E2-S4 | Make document verification decisions |
| `FraudScreeningPage` | E3-S3 | View fraud evaluation results |
| `AssessmentPage` | E4-S3 | Submit assessment decision |
| `SettlementPage` | E5-S3 | Confirm settlement (admin) |
| `DisputePage` | E6-S1, E6-S2 | File dispute or reopen request |
| `OverridePage` | E7-S3 | Submit admin override (admin only) |
| `AuditTrailPage` | E7-S2 | View complete audit history |

---

## Backend Services Summary

| Service | Story | Purpose |
|---------|-------|---------|
| `PolicyService` | E1-S1 | Validate policy active date |
| `FraudService` | E3-S1 | Evaluate claim against fraud rules |
| `AssessmentService` | E4-S1 | Evaluate coverage status |
| `PayoutService` | E4-S2 | Calculate payable amount |
| `SettlementService` | E5-S2 | Generate settlement records |
| `DisputeService` | E6-S1 | Create sub-claims |
| `OverrideService` | E7-S1 | Admin override decisions |
| `AuditService` | E7-S2 | Record audit trail entries |

---

## Backend Repositories Summary

| Repository | Purpose |
|------------|---------|
| `ClaimRepository` | Claim CRUD + state transitions |
| `PolicyRepository` | Policy lookups |
| `DocumentRepository` | Document CRUD + verification |
| `AssessmentRepository` | Assessment immutable recording |
| `FraudRepository` | Fraud screening result recording |
| `SettlementRepository` | Settlement WORM ledger |
| `SubClaimRepository` | Sub-claim creation |
| `OverrideRepository` | Override audit log (immutable) |
| `AuditRepository` | Audit trail (append-only) |

---

## Summary

Total files across all stories:

| Category | Count |
|----------|-------|
| Backend routes | 9 |
| Backend services | 8 |
| Backend repositories | 9 |
| Backend utilities | 4 |
| Backend database models | 1 (consolidated) |
| Backend tests | 14+ |
| Frontend pages | 11 |
| Frontend components | 15+ |
| Frontend API clients | 8 |
| Frontend tests | 8+ |
| **Total implementation files** | **~90** |

All files are mapped to specific stories and acceptance criteria for traceability.
