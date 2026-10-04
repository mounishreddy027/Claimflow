from datetime import date
from typing import Optional


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


# === E1-S1: Policy Active Date Validation ===
class PolicyNotActiveException(Exception):
    def __init__(
        self,
        policy_number: str,
        incident_date: date,
        effective_date: date,
        expiry_date: Optional[date],
        reason_code: str,
    ) -> None:
        self.policy_number = policy_number
        self.incident_date = incident_date
        self.effective_date = effective_date
        self.expiry_date = expiry_date
        self.reason_code = reason_code

        message = (
            f"Policy {policy_number} is not active for incident on {incident_date}. "
            f"Policy effective {effective_date} to {expiry_date}. "
            f"Reason: {reason_code}"
        )
        super().__init__(message)
# === END E1-S1 ===


# === E4-S1: Coverage Assessment ===
class CoverageDefinitionNotFoundError(ValueError):
    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id
        super().__init__(f"Coverage definition not found for policy: {policy_id}")
# === END E4-S1 ===
