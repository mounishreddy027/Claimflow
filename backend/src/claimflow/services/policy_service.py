from datetime import date
from typing import Any

from claimflow.types.exceptions import PolicyNotActiveException


class PolicyService:
    def validate_active(self, policy: dict[str, Any], incident_date: date) -> bool:
        """
        Validate if a policy is active on the given incident date.

        Policy is active if:
        - incident_date >= effective_date AND
        - (expiry_date is None OR incident_date <= expiry_date)

        Args:
            policy: Policy dict with policy_number, effective_date, expiry_date
            incident_date: Date of incident

        Returns:
            True if policy is active

        Raises:
            PolicyNotActiveException: If policy is not active
        """
        policy_number: str = policy["policy_number"]
        effective_date: date = policy["effective_date"]
        expiry_date: date | None = policy["expiry_date"]

        if incident_date < effective_date:
            raise PolicyNotActiveException(
                policy_number=policy_number,
                incident_date=incident_date,
                effective_date=effective_date,
                expiry_date=expiry_date,
                reason_code="POLICY_NOT_EFFECTIVE",
            )

        if expiry_date is not None and incident_date > expiry_date:
            raise PolicyNotActiveException(
                policy_number=policy_number,
                incident_date=incident_date,
                effective_date=effective_date,
                expiry_date=expiry_date,
                reason_code="POLICY_EXPIRED",
            )

        return True
