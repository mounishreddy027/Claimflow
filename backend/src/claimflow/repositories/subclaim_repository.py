from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class SubClaim:
    """Linked sub-claim spawned upon reopening a settled claim (AC-08)."""

    sub_claim_id: str
    parent_claim_id: str
    disputed_amount: Decimal
    dispute_reason: str
    dispute_category: str
    status: str = "UNDER_REVIEW"
    reopened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SubClaimRepository:
    """Repository storing linked sub-claims for dispute recourse."""

    def __init__(self) -> None:
        self._storage: dict[str, SubClaim] = {}

    def create_subclaim(self, subclaim: SubClaim) -> SubClaim:
        """Store a new linked sub-claim."""
        self._storage[subclaim.sub_claim_id] = subclaim
        return subclaim

    def get_by_id(self, sub_claim_id: str) -> SubClaim | None:
        """Fetch sub-claim by ID."""
        return self._storage.get(sub_claim_id)

    def get_by_parent_claim_id(self, parent_claim_id: str) -> list[SubClaim]:
        """Fetch all sub-claims linked to a parent claim."""
        return [s for s in self._storage.values() if s.parent_claim_id == parent_claim_id]
