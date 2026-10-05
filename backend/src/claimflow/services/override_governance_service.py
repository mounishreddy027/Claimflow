from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar

from claimflow.domain.claim import Claim
from claimflow.types.enums import ActorRole
from claimflow.utils.financial import to_decimal


@dataclass(frozen=True)
class OverrideGovernanceCheck:
    """Outcome of governance evaluation for an administrative override."""

    is_permitted: bool
    requires_dual_approval: bool
    allowed_reason_codes: list[str]
    rejection_reason: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class OverrideGovernanceService:
    """
    Segregation of Duties (SoD) and governance engine governing administrative overrides.
    Enforces four-eyes principle (dual sign-off for large overrides) and valid reason catalogs.
    """

    DUAL_APPROVAL_THRESHOLD: ClassVar[Decimal] = Decimal("10000.00")

    VALID_REASON_CODES: ClassVar[set[str]] = {
        "ADM_OVR_FRAUD_CLEARED_01",
        "ADM_OVR_FRAUD_FLAG_02",
        "ADM_OVR_SPECIAL_DISPENSATION_03",
        "ADM_OVR_REGULATORY_MANDATE_04",
        "ADM_OVR_EX_GRATIA_SETTLEMENT_05",
    }

    def evaluate_override_eligibility(
        self,
        claim: Claim,
        actor_role: ActorRole | str,
        reason_code: str,
        comment: str,
    ) -> OverrideGovernanceCheck:
        """Evaluate if an administrator is permitted to execute an override decision."""
        role_str = getattr(actor_role, "value", str(actor_role))

        # 1. Segregation of Duties: Only ROLE_ADMIN or ADMIN is permitted
        if role_str not in {"ROLE_ADMIN", "ADMIN"}:
            return OverrideGovernanceCheck(
                is_permitted=False,
                requires_dual_approval=False,
                allowed_reason_codes=list(self.VALID_REASON_CODES),
                rejection_reason=f"Actor role '{role_str}' lacks administrative override privilege",
            )

        # 2. Reason code validity
        if reason_code not in self.VALID_REASON_CODES:
            return OverrideGovernanceCheck(
                is_permitted=False,
                requires_dual_approval=False,
                allowed_reason_codes=list(self.VALID_REASON_CODES),
                rejection_reason=f"Reason code '{reason_code}' is not in approved governance catalog",
            )

        # 3. Mandatory justification comment
        if len(comment.strip()) < 10:
            return OverrideGovernanceCheck(
                is_permitted=False,
                requires_dual_approval=False,
                allowed_reason_codes=list(self.VALID_REASON_CODES),
                rejection_reason="Audit comment must contain at least 10 characters of justification",
            )

        # 4. Four-Eyes check for high-value claims
        requires_dual = to_decimal(claim.claim_amount) >= self.DUAL_APPROVAL_THRESHOLD

        return OverrideGovernanceCheck(
            is_permitted=True,
            requires_dual_approval=requires_dual,
            allowed_reason_codes=list(self.VALID_REASON_CODES),
            rejection_reason=None,
        )
