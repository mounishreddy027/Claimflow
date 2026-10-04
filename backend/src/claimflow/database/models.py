from dataclasses import dataclass
from datetime import datetime


# === E3-S2: Fraud Rules Configuration ===
@dataclass(frozen=True)
class FraudRuleVersion:
    """Immutable fraud rule version record for audit trail."""
    version_number: str
    effective_date: str
    lob: str
    rules_json: str
    created_by_admin_id: str | None = None
    is_current: bool = True
    created_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "version_number": self.version_number,
            "effective_date": self.effective_date,
            "lob": self.lob,
            "rules_json": self.rules_json,
            "created_by_admin_id": self.created_by_admin_id,
            "is_current": self.is_current,
            "created_at": self.created_at,
        }


# === END E3-S2 ===


# === E4-S1: Coverage Assessment ===
@dataclass(frozen=True)
class CoverageAssessment:
    """Immutable coverage assessment result."""
    is_covered: bool
    coverage_reason_code: str
    assessed_at: datetime
# === END E4-S1 ===
