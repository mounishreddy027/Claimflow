from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from claimflow.api.dependencies import (
    get_assessment_engine,
    get_claim_repository,
    get_policy_repository,
    get_settlement_service,
)
from claimflow.api.schemas import SettlementResponse
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.policy_repository import PolicyRepository
from claimflow.services.assessment_engine import AssessmentEngine
from claimflow.services.settlement_service import SettlementService
from claimflow.types.enums import ActorRole, ClaimState
from claimflow.types.exceptions import PayoutInvariantViolationException
from claimflow.utils.financial import to_decimal

router = APIRouter(prefix="/api/v1/claims", tags=["settlement"])


@router.post("/{claim_id}/settle", response_model=SettlementResponse)
def settle_claim(
    claim_id: str,
    x_actor_role: Annotated[str | None, Header()] = None,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    policy_repo: PolicyRepository = Depends(get_policy_repository),
    assessment_engine: AssessmentEngine = Depends(get_assessment_engine),
    settlement_service: SettlementService = Depends(get_settlement_service),
) -> SettlementResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.current_state != ClaimState.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot settle claim in state {claim.current_state.value}. Must be in APPROVED state.",
        )

    policy = policy_repo.get_policy(claim.policy_number)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {claim.policy_number} not found")

    assessment = assessment_engine.assess(
        claim_id=claim_id,
        claim_amount=claim.claim_amount,
        sum_insured=to_decimal(policy["sum_insured"]),
        deductible=to_decimal(policy.get("deductible", Decimal("0.00"))),
        copay_percent=to_decimal(policy.get("copay_percent", Decimal("0.00"))),
        assessed_by="assessor",
    )

    try:
        payout = settlement_service.settle_claim(
            claim_id=claim_id,
            assessment=assessment,
            requested_payout=assessment.payable_amount,
            actor_id="system_payout",
            actor_role=ActorRole.SYSTEM,
        )
    except PayoutInvariantViolationException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SettlementResponse(
        payoutId=payout.payout_id,
        claimId=payout.claim_id,
        payoutAmount=payout.payout_amount,
        currency=payout.currency,
        status=payout.status.value,
        disbursementRail=payout.disbursement_rail,
        recipientMaskedAccount=payout.recipient_masked_account,
        settledAt=payout.settled_at,
    )
