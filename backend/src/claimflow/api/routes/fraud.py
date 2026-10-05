from fastapi import APIRouter, Depends, HTTPException

from claimflow.api.dependencies import (
    get_claim_repository,
    get_fraud_service,
    get_policy_repository,
)
from claimflow.api.schemas import FraudScreenRequest, FraudScreenResponse
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.policy_repository import PolicyRepository
from claimflow.services.fraud_service import FraudService

router = APIRouter(prefix="/api/v1/claims", tags=["fraud"])


@router.post("/{claim_id}/fraud-screen", response_model=FraudScreenResponse)
def evaluate_claim_fraud(
    claim_id: str,
    req: FraudScreenRequest = FraudScreenRequest(),
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    policy_repo: PolicyRepository = Depends(get_policy_repository),
    fraud_service: FraudService = Depends(get_fraud_service),
) -> FraudScreenResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    policy = policy_repo.get_policy(claim.policy_number)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {claim.policy_number} not found")

    # Count other claims on the same policy
    all_claims = claim_repo.list_claims()
    prior_claims = sum(
        1 for c in all_claims
        if c.policy_number == claim.policy_number and c.claim_id != claim_id
    )

    result = fraud_service.evaluate_fraud(
        claim=claim,
        policy=policy,
        prior_claims_count=prior_claims,
        incident_hour=req.incidentHour,
        force_deterministic=req.forceDeterministic,
    )

    return FraudScreenResponse(
        reportId=result.report_id,
        claimId=result.claim_id,
        policyVersion=result.policy_version,
        fraudScore=result.fraud_score,
        policyThreshold=result.policy_threshold,
        isFlagged=result.is_flagged,
        evaluationMode=result.evaluation_mode,
        aiAnalysis=result.ai_analysis,
        aiConfidence=result.ai_confidence,
        triggeredRules=result.triggered_rules,
        evaluatedAt=result.evaluated_at,
    )


@router.get("/{claim_id}/fraud-screen", response_model=FraudScreenResponse)
def get_claim_fraud_screen(
    claim_id: str,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    policy_repo: PolicyRepository = Depends(get_policy_repository),
    fraud_service: FraudService = Depends(get_fraud_service),
) -> FraudScreenResponse:
    return evaluate_claim_fraud(
        claim_id=claim_id,
        req=FraudScreenRequest(forceDeterministic=False),
        claim_repo=claim_repo,
        policy_repo=policy_repo,
        fraud_service=fraud_service,
    )
