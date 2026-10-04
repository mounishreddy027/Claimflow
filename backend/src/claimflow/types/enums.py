from enum import Enum


class ClaimType(str, Enum):
    MOTOR = "MOTOR"
    HEALTH = "HEALTH"
    LIFE = "LIFE"


# === E1-S1: Policy Active Date Validation ===
class PolicyRejectReason(str, Enum):
    """Reason codes for policy rejection due to inactivity."""

    POLICY_EXPIRED = "POLICY_EXPIRED"
    POLICY_NOT_EFFECTIVE = "POLICY_NOT_EFFECTIVE"
# === END E1-S1 ===


# === E4-S1: Coverage Assessment ===
class CoverageReasonCode(str, Enum):
    CLAIM_TYPE_NOT_COVERED = "CLAIM_TYPE_NOT_COVERED"
    POLICY_EXCLUSION = "POLICY_EXCLUSION"
    COVERAGE_VERIFIED = "COVERAGE_VERIFIED"
# === END E4-S1 ===


# === E2-S1: Document Checklist ===
class DocumentType(str, Enum):
    """Document type enumeration for claim documents."""

    POLICE_FIR = "POLICE_FIR"
    REPAIR_INVOICE = "REPAIR_INVOICE"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    HOSPITAL_BILL = "HOSPITAL_BILL"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    DEATH_CERTIFICATE = "DEATH_CERTIFICATE"
    AUTOPSY_REPORT = "AUTOPSY_REPORT"


# === END E2-S1 ===


# === E3-S2: Fraud Rules Configuration ===
class LOB(str, Enum):
    """Line of Business enumeration for fraud rule configuration."""
    MOTOR = "Motor"
    HEALTH = "Health"
    LIFE = "Life"


# === END E3-S2 ===


# === E7-S2 & Core Lifecycle Enums ===
class OperationType(str, Enum):
    CLAIM_CREATED = "CLAIM_CREATED"
    STATE_TRANSITION = "STATE_TRANSITION"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED"
    FRAUD_EVALUATED = "FRAUD_EVALUATED"
    ASSESSMENT_SUBMITTED = "ASSESSMENT_SUBMITTED"
    SETTLEMENT_CONFIRMED = "SETTLEMENT_CONFIRMED"
    OVERRIDE_APPLIED = "OVERRIDE_APPLIED"
    CLAIM_REOPENED = "CLAIM_REOPENED"


class ActorRole(str, Enum):
    CLAIMANT = "CLAIMANT"
    CUSTOMER = "CUSTOMER"
    ASSESSOR = "ASSESSOR"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"


class ClaimState(str, Enum):
    FILED = "FILED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"
    REOPENED = "REOPENED"


class AdjudicationDecision(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECT = "REJECT"


class PayoutStatus(str, Enum):
    PENDING = "PENDING"
    DISBURSED = "DISBURSED"
    FAILED = "FAILED"


class ChecklistStatus(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    DEFICIENT = "DEFICIENT"

