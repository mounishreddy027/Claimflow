from datetime import date


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""


# === E3-S2: Fraud Rules Configuration ===
# === END E3-S2 ===


# === E1-S1: Policy Active Date Validation ===
class PolicyNotActiveException(Exception):
    def __init__(
        self,
        policy_number: str,
        incident_date: date,
        effective_date: date,
        expiry_date: date | None,
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


class PolicyNotFoundError(Exception):
    def __init__(self, policy_number: str) -> None:
        self.policy_number = policy_number
        super().__init__(f"Policy {policy_number} not found in policy registry")
# === END E1-S1 ===


# === E4-S1: Coverage Assessment ===
class CoverageDefinitionNotFoundError(ValueError):
    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id
        super().__init__(f"Coverage definition not found for policy: {policy_id}")
# === END E4-S1 ===


# === E7-S2 & Core Lifecycle Exceptions ===
class ImmutabilityViolationError(Exception):
    """Raised when an attempt is made to update or delete immutable records."""


class AuditIntegrityError(Exception):
    """Raised when the hash chain or audit log entry fails integrity validation."""


from collections.abc import Sequence


class InvalidClaimStateException(Exception):
    """Raised when an illegal claim state transition is attempted."""

    def __init__(
        self,
        claim_id: str,
        current_state: object,
        attempted_target_state: object,
        allowed_target_states: Sequence[object],
    ) -> None:
        self.claim_id = claim_id
        self.current_state = current_state
        self.attempted_target_state = attempted_target_state
        self.allowed_target_states = list(allowed_target_states)
        curr_val = getattr(current_state, "value", str(current_state))
        att_val = getattr(attempted_target_state, "value", str(attempted_target_state))
        allowed_vals = [getattr(s, "value", str(s)) for s in allowed_target_states]
        message = (
            f"Cannot transition claim {claim_id} from {curr_val} to "
            f"{att_val}. Valid target states: {allowed_vals}"
        )
        super().__init__(message)


class PayoutInvariantViolationException(Exception):
    """Raised when payout amount does not equal assessed payable amount."""

