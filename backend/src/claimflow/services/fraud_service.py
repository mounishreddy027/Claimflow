from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import cast
from uuid import uuid4

from claimflow.domain.claim import Claim
from claimflow.utils.financial import to_decimal


@dataclass(frozen=True)
class FraudScreeningResult:
    """Deterministic fraud evaluation result (AC-04)."""

    report_id: str
    claim_id: str
    policy_version: int
    fraud_score: int
    policy_threshold: int
    is_flagged: bool
    triggered_rules: list[dict[str, object]] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FraudService:
    """Deterministic rule-based fraud screening engine."""

    def evaluate_fraud(
        self,
        claim: Claim,
        policy: Mapping[str, object],
        prior_claims_count: int = 0,
        incident_hour: int | None = None,
    ) -> FraudScreeningResult:
        """Compute deterministic aggregate fraud score and evaluate threshold flagging."""
        triggered: list[dict[str, object]] = []
        score = 0

        effective_date = cast(date, policy["effective_date"])
        sum_insured = to_decimal(cast(Decimal, policy["sum_insured"]))
        threshold = int(cast(int, policy.get("fraud_threshold", 50)))
        policy_version = int(cast(int, policy.get("version", 1)))

        # FR-01: Rapid Inception Loss (+25 pts)
        days_from_start = (claim.incident_date - effective_date).days
        if 0 <= days_from_start <= 14:
            score += 25
            triggered.append({
                "ruleId": "FR-01",
                "weight": 25,
                "reasonCode": "FRAUD_RAPID_INCEPTION",
                "description": "Incident occurred within 14 calendar days of policy start",
            })

        # FR-02: Near-Ceiling Claim Amount (+20 pts)
        if claim.claim_amount > (Decimal("0.90") * sum_insured):
            score += 20
            triggered.append({
                "ruleId": "FR-02",
                "weight": 20,
                "reasonCode": "FRAUD_HIGH_SUM_RATIO",
                "description": "Claim amount exceeds 90% of policy sum insured",
            })

        # FR-03: High Claim Frequency (+20 pts)
        if prior_claims_count >= 2:
            score += 20
            triggered.append({
                "ruleId": "FR-03",
                "weight": 20,
                "reasonCode": "FRAUD_REPEAT_CLAIMANT",
                "description": "Policy has had >= 2 claims filed within preceding 12 months",
            })

        # FR-04: Off-Hours Incident (+15 pts)
        if incident_hour is not None and incident_hour in {23, 0, 1, 2, 3, 4}:
            score += 15
            triggered.append({
                "ruleId": "FR-04",
                "weight": 15,
                "reasonCode": "FRAUD_OFF_HOURS_INCIDENT",
                "description": "Incident recorded between 23:00 and 04:00 local time",
            })

        # FR-05: Round Number Claim Amount (+10 pts)
        if claim.claim_amount > 0 and (claim.claim_amount % Decimal("1000.00")) == Decimal("0.00"):
            score += 10
            triggered.append({
                "ruleId": "FR-05",
                "weight": 10,
                "reasonCode": "FRAUD_ROUND_AMOUNT",
                "description": "Claim amount is an exact multiple of 1,000 without itemized cents",
            })

        # FR-06: Delayed Reporting (+10 pts)
        filing_date = claim.created_at.date()
        if (filing_date - claim.incident_date).days > 30:
            score += 10
            triggered.append({
                "ruleId": "FR-06",
                "weight": 10,
                "reasonCode": "FRAUD_DELAYED_REPORTING",
                "description": "More than 30 days elapsed between incident date and initial filing",
            })

        final_score = min(100, score)
        is_flagged = final_score > threshold

        return FraudScreeningResult(
            report_id=f"FRD-{uuid4().hex[:8].upper()}",
            claim_id=claim.claim_id,
            policy_version=policy_version,
            fraud_score=final_score,
            policy_threshold=threshold,
            is_flagged=is_flagged,
            triggered_rules=triggered,
            evaluated_at=datetime.now(timezone.utc),
        )
