"""
Integration test verifying live, non-deterministic AI evaluation using Google Gemini.
Executes an actual network call to the Gemini API using GEMINI_API_KEY from .env.
"""

import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from dotenv import load_dotenv

from claimflow.config.env import get_ai_config
from claimflow.domain.claim import Claim
from claimflow.services.fraud_service import FraudService
from claimflow.types.enums import ClaimType

# Ensure .env is loaded
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@pytest.mark.integration
@pytest.mark.AC_04
def test_live_gemini_ai_fraud_evaluation() -> None:
    """Execute real live non-deterministic AI call to Gemini."""
    cfg = get_ai_config()
    api_key = cfg.get("api_key")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not found in environment or .env")

    service = FraudService(force_deterministic=False)

    claim = Claim(
        claim_id="CLM-LIVE-AI-999",
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("4750.00"),
        incident_date=date(2026, 6, 1),
        incident_description=(
            "Single vehicle crash on dark rural road at 2:30 AM. "
            "Driver claims deer jumped in front of vehicle, resulting in direct impact with utility pole. "
            "No witnesses and no police report filed at the scene."
        ),
        created_at=datetime.now(timezone.utc),
    )

    policy = {
        "policy_number": "POL-MTR-1001",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("50000.00"),
        "fraud_threshold": 45,
        "version": 1,
    }

    result = service.evaluate_fraud(claim, policy, prior_claims_count=1, incident_hour=2)

    # Assert that this was genuinely executed by AI, NOT the deterministic fallback
    assert result.evaluation_mode == "AI_POWERED", f"Expected AI_POWERED, got {result.evaluation_mode}"
    assert result.ai_analysis is not None
    assert len(result.ai_analysis) > 30, "AI explanation should provide descriptive reasoning"
    assert result.ai_confidence is not None and result.ai_confidence > 0.5
    assert 0 <= result.fraud_score <= 100
    assert result.is_flagged == (result.fraud_score > 45)

    print("\n--- Live Gemini AI Fraud Result ---")
    print(f"Mode: {result.evaluation_mode}")
    print(f"Fraud Score: {result.fraud_score} (Threshold: {result.policy_threshold})")
    print(f"Flagged: {result.is_flagged}")
    print(f"Confidence: {result.ai_confidence}")
    print(f"AI Analysis: {result.ai_analysis}")
