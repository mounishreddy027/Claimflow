#!/usr/bin/env python3
"""
scripts/check_gemini.py — Quick Gemini API Verification Script
Tests API key validity, latency, and live AI fraud analysis.
"""

import os
import sys
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from claimflow.config.env import get_ai_config
from claimflow.domain.claim import Claim
from claimflow.services.fraud_service import FraudService
from claimflow.types.enums import ClaimType


def main() -> None:
    print("=" * 65)
    print(" ClaimFlow Gemini API Live Diagnostic Check")
    print("=" * 65)

    # 1. Inspect Environment Config
    cfg = get_ai_config()
    api_key = cfg.get("api_key")
    provider = cfg.get("provider")
    model = cfg.get("model")

    print(f"Provider : {provider}")
    print(f"Model    : {model}")

    if not api_key:
        print("\n[FAIL] No API key detected in .env file.")
        print("Please add GEMINI_API_KEY=\"your_key_here\" into your .env file.")
        sys.exit(1)

    masked_key = f"{api_key[:6]}...{api_key[-4:]}"
    print(f"API Key  : {masked_key} (detected)")
    print("-" * 65)

    # 2. Execute Live Call
    print(f"Connecting to Google Gemini API ({model})...")
    start = time.perf_counter()

    sample_claim = Claim(
        claim_id="CLM-DIAG-001",
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("4200.00"),
        incident_date=date(2026, 6, 1),
        incident_description=(
            "Vehicle collided with a concrete barrier on highway ramp at 1:45 AM. "
            "Driver reports momentary loss of control due to wet asphalt. "
            "No other vehicles involved; solitary driver with no passengers."
        ),
        created_at=datetime.now(timezone.utc),
    )

    sample_policy = {
        "policy_number": "POL-MTR-1001",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("50000.00"),
        "fraud_threshold": 45,
        "version": 1,
    }

    try:
        service = FraudService(force_deterministic=False)
        result = service.evaluate_fraud(sample_claim, sample_policy, prior_claims_count=1, incident_hour=1)
        latency = (time.perf_counter() - start) * 1000.0

        print(f"[OK] Response received in {latency:.1f}ms!\n")

        if result.evaluation_mode == "AI_POWERED":
            print("[SUCCESS] Gemini API is working properly in AI_POWERED mode!")
            print(f"  - Fraud Risk Score : {result.fraud_score} / 100 (Threshold: {result.policy_threshold})")
            print(f"  - Flagged for Review: {result.is_flagged}")
            print(f"  - Model Confidence : {result.ai_confidence}")
            print(f"\nAI Analysis & Explanation:\n  \"{result.ai_analysis}\"\n")
            if result.triggered_rules:
                print("Triggered Risk Indicators:")
                for r in result.triggered_rules:
                    print(f"  * [{r.get('ruleId')}] {r.get('reasonCode')}: {r.get('description')}")
        else:
            print("[WARNING] Evaluation completed but fell back to DETERMINISTIC_FALLBACK mode.")
            print(f"  - Reason: {result.ai_analysis}")
            sys.exit(1)

    except Exception as exc:
        print(f"\n[FAIL] Error communicating with Gemini API: {exc}")
        sys.exit(1)

    print("=" * 65)


if __name__ == "__main__":
    main()
