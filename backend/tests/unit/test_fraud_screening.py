from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from claimflow.domain.claim import Claim
from claimflow.services.fraud_service import FraudService
from claimflow.types.enums import ClaimType

pytestmark = pytest.mark.AC_04


def test_low_risk_claim_scores_below_threshold() -> None:
    service = FraudService()
    claim = Claim(
        claim_id="CLM-LOW-01",
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("1500.25"),
        incident_date=date(2026, 6, 20),
        incident_description="Minor door dent",
        created_at=datetime(2026, 6, 25, tzinfo=timezone.utc),
    )
    policy = {
        "policy_number": "POL-MTR-1001",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("50000.00"),
        "fraud_threshold": 50,
        "version": 1,
    }

    result = service.evaluate_fraud(claim, policy, prior_claims_count=0)
    assert result.fraud_score == 0
    assert result.is_flagged is False
    assert len(result.triggered_rules) == 0


def test_high_risk_claim_exceeding_threshold() -> None:
    # FR-01: incident within 14 days of inception (+25)
    # FR-02: claim > 90% of sum insured (+20)
    # Total = 45 > threshold 40 -> is_flagged = True
    service = FraudService()
    claim = Claim(
        claim_id="CLM-HIGH-01",
        policy_number="POL-HLT-2002",
        claim_type=ClaimType.HEALTH,
        claim_amount=Decimal("9500.00"),
        incident_date=date(2026, 1, 5),
        incident_description="Emergency hospital admission",
        created_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
    )
    policy = {
        "policy_number": "POL-HLT-2002",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("10000.00"),
        "fraud_threshold": 40,
        "version": 1,
    }

    result = service.evaluate_fraud(claim, policy, prior_claims_count=0)
    assert result.fraud_score == 45
    assert result.is_flagged is True
    trigger_codes = [r["reasonCode"] for r in result.triggered_rules]
    assert "FRAUD_RAPID_INCEPTION" in trigger_codes
    assert "FRAUD_HIGH_SUM_RATIO" in trigger_codes


def test_boundary_condition_score_equals_threshold() -> None:
    # Exactly 50 points with threshold 50 -> is_flagged is FALSE (strictly exceeds)
    service = FraudService()
    claim = Claim(
        claim_id="CLM-BOUND-01",
        policy_number="POL-MTR-3003",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("5000.00"),  # FR-05: round number (+10)
        incident_date=date(2026, 1, 10),  # FR-01: within 14 days of start date (+25)
        incident_description="Damage",
        created_at=datetime(2026, 1, 11, 23, 30, tzinfo=timezone.utc),  # FR-04: off-hours (+15)
    )
    policy = {
        "policy_number": "POL-MTR-3003",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("20000.00"),
        "fraud_threshold": 50,
        "version": 1,
    }

    # Total score = 25 (FR-01) + 15 (FR-04) + 10 (FR-05) = 50
    result = service.evaluate_fraud(claim, policy, prior_claims_count=0, incident_hour=23)
    assert result.fraud_score == 50
    assert result.policy_threshold == 50
    assert result.is_flagged is False


def test_policy_version_sensitivity() -> None:
    service = FraudService()
    claim = Claim(
        claim_id="CLM-VERS-01",
        policy_number="POL-LIF-4004",
        claim_type=ClaimType.LIFE,
        claim_amount=Decimal("95000.50"),  # FR-02: > 90% (+20)
        incident_date=date(2026, 5, 1),
        incident_description="Loss",
        created_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    policy_v1 = {
        "policy_number": "POL-LIF-4004",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("100000.00"),
        "fraud_threshold": 50,
        "version": 1,
    }
    policy_v2 = {
        "policy_number": "POL-LIF-4004",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("100000.00"),
        "fraud_threshold": 35,
        "version": 2,
    }

    # Prior claims = 2 -> triggers FR-03 (+20)
    # Total = 20 (FR-02) + 20 (FR-03) = 40
    res_v1 = service.evaluate_fraud(claim, policy_v1, prior_claims_count=2)
    assert res_v1.fraud_score == 40
    assert res_v1.is_flagged is False

    res_v2 = service.evaluate_fraud(claim, policy_v2, prior_claims_count=2)
    assert res_v2.fraud_score == 40
    assert res_v2.is_flagged is True
