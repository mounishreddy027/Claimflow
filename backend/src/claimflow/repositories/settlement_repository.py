from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from claimflow.types.enums import PayoutStatus
from claimflow.types.exceptions import ImmutabilityViolationError


@dataclass(frozen=True)
class PayoutRecord:
    """Immutable payout disbursement record (AC-07, NFR-02)."""

    payout_id: str
    claim_id: str
    payout_amount: Decimal
    currency: str = "USD"
    status: PayoutStatus = PayoutStatus.DISBURSED
    disbursement_rail: str = "STUBBED_ACH"
    recipient_masked_account: str = "XXXX-XXXX-1926"
    settled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SettlementRepository:
    """Append-only WORM ledger for immutable settlement payouts."""

    def __init__(self) -> None:
        self._storage: list[PayoutRecord] = []

    def append(self, payout: PayoutRecord) -> PayoutRecord:
        """Store immutable payout record."""
        self._storage.append(payout)
        return payout

    def get_by_id(self, payout_id: str) -> PayoutRecord | None:
        """Look up payout record by ID."""
        for p in self._storage:
            if p.payout_id == payout_id:
                return p
        return None

    def get_by_claim_id(self, claim_id: str) -> list[PayoutRecord]:
        """Retrieve all payouts for a claim."""
        return [p for p in self._storage if p.claim_id == claim_id]

    def update(self, payout_id: str, updates: Mapping[str, object]) -> None:
        """Blocked: Payout records are immutable."""
        raise ImmutabilityViolationError(
            f"Payout records are immutable. Modification rejected for payout_id {payout_id}"
        )

    def delete(self, payout_id: str) -> None:
        """Blocked: Payout records cannot be deleted."""
        raise ImmutabilityViolationError(
            f"Payout records are immutable. Deletion rejected for payout_id {payout_id}"
        )
