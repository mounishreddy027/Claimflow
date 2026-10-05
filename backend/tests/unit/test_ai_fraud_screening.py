import json
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from claimflow.domain.claim import Claim
from claimflow.services.fraud_service import FraudService
from claimflow.types.enums import ClaimType

pytestmark = pytest.mark.AC_04


@pytest.fixture
def sample_claim() -> Claim:
    return Claim(
        claim_id="CLM-AI-001",
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("3500.00"),
        incident_date=date(2026, 6, 1),
        incident_description="Rear-end collision during rush hour",
        created_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_policy() -> dict[str, object]:
    return {
        "policy_number": "POL-MTR-1001",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("50000.00"),
        "fraud_threshold": 40,
        "version": 1,
    }


def test_fallback_to_deterministic_when_no_api_key(
    sample_claim: Claim, sample_policy: dict[str, object]
) -> None:
    service = FraudService()
    with patch("claimflow.services.fraud_service.get_ai_config", return_value={"provider": None, "api_key": None, "model": None}):
        res = service.evaluate_fraud(sample_claim, sample_policy)
        assert res.evaluation_mode == "DETERMINISTIC_FALLBACK"
        assert res.ai_confidence == 1.0
        assert res.fraud_score >= 0


def test_fallback_to_deterministic_when_ai_raises_error(
    sample_claim: Claim, sample_policy: dict[str, object]
) -> None:
    service = FraudService()
    mock_config = {"provider": "gemini", "api_key": "test_key", "model": "gemini-2.5-flash"}
    with patch("claimflow.services.fraud_service.get_ai_config", return_value=mock_config):
        with patch.object(service, "_evaluate_with_ai", side_effect=RuntimeError("Connection timed out")):
            res = service.evaluate_fraud(sample_claim, sample_policy)
            assert res.evaluation_mode == "DETERMINISTIC_FALLBACK"
            assert res.fraud_score >= 0


def test_ai_powered_evaluation_success(
    sample_claim: Claim, sample_policy: dict[str, object]
) -> None:
    service = FraudService()
    mock_config = {"provider": "gemini", "api_key": "valid_gemini_key", "model": "gemini-2.5-flash"}
    mock_ai_json = {
        "fraud_score": 78,
        "is_flagged": True,
        "ai_analysis": "Suspicious rapid claim pattern and inconsistency in vehicle speed reported.",
        "ai_confidence": 0.94,
        "triggered_rules": [
            {
                "ruleId": "AI-ANOMALY-01",
                "weight": 35,
                "reasonCode": "NARRATIVE_INCONSISTENCY",
                "description": "Reported damage contradicts typical intersection collision physics",
            }
        ],
    }
    payload_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": json.dumps(mock_ai_json)}
                    ]
                }
            }
        ]
    }

    with patch("claimflow.services.fraud_service.get_ai_config", return_value=mock_config):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(payload_response).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_response

            res = service.evaluate_fraud(sample_claim, sample_policy)
            assert res.evaluation_mode == "AI_POWERED"
            assert res.fraud_score == 78
            assert res.is_flagged is True
            assert res.ai_confidence == 0.94
            assert "damage contradicts" in str(res.triggered_rules)


def test_force_deterministic_bypasses_ai(
    sample_claim: Claim, sample_policy: dict[str, object]
) -> None:
    service = FraudService()
    mock_config = {"provider": "gemini", "api_key": "valid_key", "model": "gemini-2.5-flash"}
    with patch("claimflow.services.fraud_service.get_ai_config", return_value=mock_config):
        with patch.object(service, "_evaluate_with_ai") as mock_ai:
            res = service.evaluate_fraud(sample_claim, sample_policy, force_deterministic=True)
            mock_ai.assert_not_called()
            assert res.evaluation_mode == "DETERMINISTIC_FALLBACK"
