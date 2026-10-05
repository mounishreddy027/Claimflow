from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from claimflow.types.enums import ClaimType


class DocumentUploadRequest(BaseModel):
    documentType: str
    fileName: str
    fileContentStub: str | None = None


class DocumentReceiptResponse(BaseModel):
    documentId: str
    documentType: str
    status: str


class ClaimIntakeRequest(BaseModel):
    policyNumber: str
    incidentDate: date
    claimType: ClaimType
    claimAmount: Decimal = Field(gt=Decimal("0.00"))
    incidentDescription: str
    supportingDocuments: list[DocumentUploadRequest] = Field(default_factory=list)


class ClaimIntakeResponse(BaseModel):
    claimId: str
    policyNumber: str
    claimType: str
    status: str
    claimAmount: Decimal
    incidentDate: date
    documentReceipts: list[DocumentReceiptResponse]
    createdAt: datetime


class StateTransitionResponse(BaseModel):
    transitionId: str
    fromState: str | None
    toState: str
    actorId: str
    actorRole: str
    reasonCode: str | None
    timestamp: datetime


class ClaimDetailResponse(BaseModel):
    claimId: str
    policyNumber: str
    claimType: str
    status: str
    claimAmount: Decimal
    incidentDate: date
    incidentDescription: str
    transitions: list[StateTransitionResponse]
    createdAt: datetime
    updatedAt: datetime


class DocumentVerifyRequest(BaseModel):
    action: str = "VERIFY"
    notes: str | None = None


class DocumentVerifyResponse(BaseModel):
    documentId: str
    status: str
    verifiedBy: str
    verifiedAt: datetime


class DocumentItemResponse(BaseModel):
    documentId: str
    documentType: str
    fileName: str
    status: str
    verifiedAt: datetime | None = None
    verifiedBy: str | None = None


class ChecklistSummaryResponse(BaseModel):
    claimId: str
    claimType: str
    checklistStatus: str
    mandatoryCount: int
    verifiedCount: int
    documents: list[DocumentItemResponse]


class AssessmentRequest(BaseModel):
    additionalDeductible: Decimal = Decimal("0.00")
    assessorNotes: str | None = None


class AssessmentResponse(BaseModel):
    assessmentId: str
    claimId: str
    claimAmount: Decimal
    sumInsured: Decimal
    effectiveClaim: Decimal
    deductibleApplied: Decimal
    copayApplied: Decimal
    grossDeductions: Decimal
    payableAmount: Decimal
    assessedAt: datetime
    assessedBy: str


class SettlementResponse(BaseModel):
    payoutId: str
    claimId: str
    payoutAmount: Decimal
    currency: str
    status: str
    disbursementRail: str
    recipientMaskedAccount: str
    settledAt: datetime


class AdminOverrideRequest(BaseModel):
    newDecision: str
    reasonCode: str
    comment: str


class AdminOverrideResponse(BaseModel):
    overrideId: str
    claimId: str
    previousDecision: str
    newDecision: str
    reasonCode: str
    comment: str
    actorId: str
    timestamp: datetime


class ReopenClaimRequest(BaseModel):
    disputeReason: str
    supplementalAmount: Decimal = Field(gt=Decimal("0.00"))
    disputeCategory: str = "SUPPLEMENTAL_DAMAGE"
    supportingDocuments: list[DocumentUploadRequest] = Field(default_factory=list)


class ReopenClaimResponse(BaseModel):
    subClaimId: str
    parentClaimId: str
    parentClaimStatus: str
    subClaimStatus: str
    disputedAmount: Decimal
    disputeReason: str
    reopenedAt: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auditId: str = Field(alias="audit_id")
    correlationId: str = Field(alias="correlation_id")
    timestamp: str
    actorId: str = Field(alias="actor_id")
    actorRole: str = Field(alias="actor_role")
    operationType: str = Field(alias="operation_type")
    claimId: str = Field(alias="claim_id")
    previousState: str | None = Field(default=None, alias="previous_state")
    newState: str | None = Field(default=None, alias="new_state")
    reasonCode: str | None = Field(default=None, alias="reason_code")
    detailJson: dict[str, object] = Field(default_factory=dict, alias="detail_json")
    previousHash: str = Field(alias="previous_hash")
    entryHash: str = Field(alias="entry_hash")


class FraudScreenRequest(BaseModel):
    forceDeterministic: bool = False
    incidentHour: int | None = None


class FraudScreenResponse(BaseModel):
    reportId: str
    claimId: str
    policyVersion: int
    fraudScore: int
    policyThreshold: int
    isFlagged: bool
    evaluationMode: str
    aiAnalysis: str | None = None
    aiConfidence: float | None = None
    triggeredRules: list[dict[str, object]]
    evaluatedAt: datetime


class PolicyItemResponse(BaseModel):
    policyNumber: str
    lineOfBusiness: str
    status: str
    effectiveDate: date
    expiryDate: date | None = None
    sumInsured: Decimal
    deductible: Decimal
    copayPercent: Decimal
    fraudThreshold: int


class SystemConfigResponse(BaseModel):
    aiConfigured: bool
    aiProvider: str | None
    aiModel: str | None
    fallbackEngine: str

