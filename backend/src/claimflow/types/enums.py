from enum import Enum


class ClaimType(str, Enum):
    MOTOR = "MOTOR"
    HEALTH = "HEALTH"
    LIFE = "LIFE"


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
