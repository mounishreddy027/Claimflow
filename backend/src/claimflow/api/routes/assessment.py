from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from claimflow.api.dependencies import (
    get_assessment_engine,
    get_claim_repository,
    get_policy_repository,
)
from claimflow.api.schemas import AssessmentRequest, AssessmentResponse
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.policy_repository import PolicyRepository
from claimflow.services.assessment_engine import AssessmentEngine
from claimflow.types.enums import ActorRole, ClaimState
from claimflow.utils.financial import to_decimal

router = APIRouter(prefix="/api/v1/claims", tags=["assessment"])


@router.post("/{claim_id}/assess", response_model=AssessmentResponse)
def assess_claim(
    claim_id: str,
    req: AssessmentRequest = AssessmentRequest(),
    x_actor_role: Annotated[str | None, Header()] = None,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    policy_repo: PolicyRepository = Depends(get_policy_repository),
    assessment_engine: AssessmentEngine = Depends(get_assessment_engine),
) -> AssessmentResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    policy = policy_repo.get_policy(claim.policy_number)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {claim.policy_number} not found")

    sum_insured = to_decimal(policy["sum_insured"])
    deductible = to_decimal(policy.get("deductible", Decimal("0.00")))
    copay_percent = to_decimal(policy.get("copay_percent", Decimal("0.00")))

    assessor_id = "assessor_user_1"
    assessment = assessment_engine.assess(
        claim_id=claim_id,
        claim_amount=claim.claim_amount,
        sum_insured=sum_insured,
        deductible=deductible,
        copay_percent=copay_percent,
        additional_deductible=req.additionalDeductible,
        assessed_by=assessor_id,
        notes=req.assessorNotes,
    )

    # Transition claim if under review
    if claim.current_state == ClaimState.UNDER_REVIEW:
        target = ClaimState.APPROVED if assessment.payable_amount > Decimal("0.00") else ClaimState.REJECTED
        reason = "POL_APPR_STP_01" if target == ClaimState.APPROVED else "POL_REJ_ZERO_PAYABLE_03"
        claim_repo.transition_claim_state(
            claim_id=claim_id,
            target_state=target,
            actor_id=assessor_id,
            actor_role=ActorRole.ASSESSOR,
            reason_code=reason,
        )

    return AssessmentResponse(
        assessmentId=assessment.assessment_id,
        claimId=assessment.claim_id,
        claimAmount=assessment.claim_amount,
        sumInsured=assessment.sum_insured,
        effectiveClaim=assessment.effective_claim,
        deductibleApplied=assessment.deductible_applied,
        copayApplied=assessment.copay_applied,
        grossDeductions=assessment.gross_deductions,
        payableAmount=assessment.payable_amount,
        assessedAt=assessment.assessed_at,
        assessedBy=assessment.assessed_by,
    )
