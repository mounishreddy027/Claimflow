from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from claimflow.domain.claim import Claim
from claimflow.services.fraud_service import FraudScreeningResult
from claimflow.types.enums import ClaimState, ClaimType
from claimflow.utils.financial import to_decimal


@dataclass(frozen=True)
class SuspiciousActivityReport:
    """Statutory fraud filing for regulatory authorities (NAIC / FinCEN)."""

    sar_id: str
    claim_id: str
    policy_number: str
    filing_date: date
    fraud_score: int
    risk_level: str
    narrative_summary: str
    recommended_action: str
    statutory_deadline: date
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class LossRatioReport:
    """Financial loss ratio calculation across a portfolio or line of business."""

    lob: str
    period_start: date
    period_end: date
    total_earned_premium: Decimal
    total_incurred_claims: Decimal
    loss_ratio_percent: Decimal
    is_favorable: bool
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ComplianceService:
    """Regulatory compliance and statutory reporting engine for insurance operations."""

    SAR_THRESHOLD = 50
    STATUTORY_FILING_DAYS = 30

    def generate_sar(
        self,
        claim: Claim,
        fraud_result: FraudScreeningResult,
        filing_date: date | None = None,
    ) -> SuspiciousActivityReport | None:
        """
        Evaluate if a claim necessitates a Suspicious Activity Report (SAR).
        Mandatory for any claim with a fraud score exceeding SAR_THRESHOLD.
        """
        if fraud_result.fraud_score < self.SAR_THRESHOLD and not fraud_result.is_flagged:
            return None

        today = filing_date or datetime.now(timezone.utc).date()
        statutory_deadline = date.fromordinal(today.toordinal() + self.STATUTORY_FILING_DAYS)

        risk_level = "CRITICAL" if fraud_result.fraud_score >= 70 else "HIGH"
        summary = (
            f"Statutory referral for claim {claim.claim_id} ({claim.claim_type.value}). "
            f"Fraud score: {fraud_result.fraud_score}/{fraud_result.policy_threshold}. "
            f"Mode: {fraud_result.evaluation_mode}. Analysis: {fraud_result.ai_analysis or 'Rule anomaly triggered'}."
        )

        return SuspiciousActivityReport(
            sar_id=f"SAR-{uuid4().hex[:8].upper()}",
            claim_id=claim.claim_id,
            policy_number=claim.policy_number,
            filing_date=today,
            fraud_score=fraud_result.fraud_score,
            risk_level=risk_level,
            narrative_summary=summary,
            recommended_action="REFER_TO_SPECIAL_INVESTIGATIONS_UNIT",
            statutory_deadline=statutory_deadline,
        )

    def calculate_loss_ratio(
        self,
        lob: ClaimType,
        claims: Sequence[Claim],
        earned_premium: Decimal,
        period_start: date,
        period_end: date,
    ) -> LossRatioReport:
        """
        Compute portfolio loss ratio: (incurred claims / earned premium) * 100.
        Uses fixed-point arithmetic with zero floating-point operations.
        """
        premium = to_decimal(earned_premium)
        if premium <= Decimal("0.00"):
            raise ValueError("Earned premium must be strictly positive")

        total_incurred = Decimal("0.00")
        for c in claims:
            if c.claim_type == lob and c.current_state in {ClaimState.APPROVED, ClaimState.SETTLED}:
                total_incurred += to_decimal(c.claim_amount)

        ratio = (total_incurred / premium) * Decimal("100.00")
        rounded_ratio = to_decimal(ratio)
        is_favorable = rounded_ratio <= Decimal("65.00")

        return LossRatioReport(
            lob=lob.value,
            period_start=period_start,
            period_end=period_end,
            total_earned_premium=premium,
            total_incurred_claims=total_incurred,
            loss_ratio_percent=rounded_ratio,
            is_favorable=is_favorable,
        )
