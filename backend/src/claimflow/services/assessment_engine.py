from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from claimflow.utils.financial import calculate_payable_amount, to_decimal


@dataclass(frozen=True)
class Assessment:
    """Immutable assessment calculation record."""

    assessment_id: str
    claim_id: str
    claim_amount: Decimal
    sum_insured: Decimal
    effective_claim: Decimal
    deductible_applied: Decimal
    copay_applied: Decimal
    gross_deductions: Decimal
    payable_amount: Decimal
    assessed_at: datetime
    assessed_by: str
    notes: str | None = None


class AssessmentEngine:
    """Financial assessment engine calculating payable amounts with strict invariants (AC-05)."""

    def assess(
        self,
        claim_id: str,
        claim_amount: Decimal,
        sum_insured: Decimal,
        deductible: Decimal,
        copay_percent: Decimal = Decimal("0.00"),
        additional_deductible: Decimal = Decimal("0.00"),
        assessed_by: str = "system",
        notes: str | None = None,
    ) -> Assessment:
        """Execute assessment calculation enforcing fixed-point math and non-negative invariant."""
        c_amt = to_decimal(claim_amount)
        s_ins = to_decimal(sum_insured)
        base_deductible = to_decimal(deductible) + to_decimal(additional_deductible)

        effective_pre = min(c_amt, s_ins)
        copay_applied = to_decimal(
            effective_pre * to_decimal(copay_percent) / Decimal("100.00")
        )

        effective, gross_ded, _, payable = calculate_payable_amount(
            claim_amount=c_amt,
            sum_insured=s_ins,
            deductible=base_deductible,
            copay=copay_applied,
        )

        return Assessment(
            assessment_id=f"ASM-{uuid4().hex[:8].upper()}",
            claim_id=claim_id,
            claim_amount=c_amt,
            sum_insured=s_ins,
            effective_claim=effective,
            deductible_applied=base_deductible,
            copay_applied=copay_applied,
            gross_deductions=gross_ded,
            payable_amount=payable,
            assessed_at=datetime.now(timezone.utc),
            assessed_by=assessed_by,
            notes=notes,
        )
