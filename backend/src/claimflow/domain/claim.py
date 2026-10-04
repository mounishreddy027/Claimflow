from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from claimflow.types.enums import ClaimState, ClaimType


@dataclass(frozen=True)
class StateTransitionRecord:
    """Immutable transition audit record."""

    transition_id: str
    claim_id: str
    from_state: str | None
    to_state: str
    actor_id: str
    actor_role: str
    timestamp: datetime
    reason_code: str | None = None


@dataclass
class Claim:
    """Claim aggregate root entity."""

    claim_id: str
    policy_number: str
    claim_type: ClaimType
    claim_amount: Decimal
    incident_date: date
    incident_description: str
    current_state: ClaimState = ClaimState.FILED
    claimant_id: str = "default_claimant"
    policy_version: int = 1
    reason_code: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    supporting_documents: list[dict[str, object]] = field(default_factory=list)
    transitions: list[StateTransitionRecord] = field(default_factory=list)
