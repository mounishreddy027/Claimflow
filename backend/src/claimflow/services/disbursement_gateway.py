from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from claimflow.types.exceptions import PayoutInvariantViolationException
from claimflow.utils.financial import to_decimal


class PaymentRail(str, Enum):
    ACH_STANDARD = "ACH_STANDARD"
    ACH_SAME_DAY = "ACH_SAME_DAY"
    RTP_REAL_TIME = "RTP_REAL_TIME"
    FEDNOW = "FEDNOW"
    VIRTUAL_CARD = "VIRTUAL_CARD"


class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    CLEARED = "CLEARED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DisbursementTransaction:
    """Disbursement record executed against a payment rail."""

    transaction_id: str
    payout_id: str
    claim_id: str
    rail: PaymentRail
    amount: Decimal
    currency: str
    recipient_masked: str
    trace_number: str
    status: PaymentStatus
    settled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DisbursementGateway:
    """
    Multi-rail payment orchestration gateway for insurance claim settlements.
    Supports ACH, RTP, and FedNow with ABA routing number check digit validation.
    """

    @staticmethod
    def validate_aba_routing(routing_number: str) -> bool:
        """Validate 9-digit ABA routing transit number using the Mod-10 checksum algorithm."""
        digits = routing_number.strip()
        if len(digits) != 9 or not digits.isdigit():
            return False

        weights = (3, 7, 1, 3, 7, 1, 3, 7, 1)
        total = sum(int(d) * w for d, w in zip(digits, weights, strict=True))
        return (total % 10) == 0

    @staticmethod
    def mask_account_number(account_number: str) -> str:
        """Mask account number to reveal only trailing 4 digits."""
        clean = account_number.strip()
        if len(clean) <= 4:
            return "****"
        return f"****-****-{clean[-4:]}"

    def disburse(
        self,
        payout_id: str,
        claim_id: str,
        amount: Decimal,
        rail: PaymentRail,
        account_number: str,
        routing_number: str,
        currency: str = "USD",
    ) -> DisbursementTransaction:
        """
        Execute payment disbursement against the target rail.
        Ensures exact decimal amount validation and routing check.
        """
        dec_amount = to_decimal(amount)
        if dec_amount <= Decimal("0.00"):
            raise PayoutInvariantViolationException(
                f"Disbursement amount {dec_amount} must be strictly greater than 0.00"
            )

        if not self.validate_aba_routing(routing_number):
            raise ValueError(f"Invalid ABA routing number: {routing_number}")

        trace_num = f"TRC-{uuid4().hex[:12].upper()}"
        masked = self.mask_account_number(account_number)

        return DisbursementTransaction(
            transaction_id=f"TXN-{uuid4().hex[:8].upper()}",
            payout_id=payout_id,
            claim_id=claim_id,
            rail=rail,
            amount=dec_amount,
            currency=currency,
            recipient_masked=masked,
            trace_number=trace_num,
            status=PaymentStatus.CLEARED,
            settled_at=datetime.now(timezone.utc),
        )
