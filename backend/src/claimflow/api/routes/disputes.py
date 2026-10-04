from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status

from claimflow.api.dependencies import get_claim_repository, get_subclaim_repository
from claimflow.api.schemas import ReopenClaimRequest, ReopenClaimResponse
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.subclaim_repository import SubClaim, SubClaimRepository
from claimflow.types.enums import ActorRole, ClaimState

router = APIRouter(prefix="/api/v1/claims", tags=["disputes"])


@router.post(
    "/{claim_id}/reopen",
    response_model=ReopenClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
def reopen_settled_claim(
    claim_id: str,
    req: ReopenClaimRequest,
    x_actor_role: Annotated[str | None, Header()] = None,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    subclaim_repo: SubClaimRepository = Depends(get_subclaim_repository),
) -> ReopenClaimResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.current_state != ClaimState.SETTLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reopen claim in state {claim.current_state.value}. Only SETTLED claims can be reopened.",
        )

    # Transition parent claim state to REOPENED
    claim_repo.transition_claim_state(
        claim_id=claim_id,
        target_state=ClaimState.REOPENED,
        actor_id="claimant_user",
        actor_role=ActorRole.CLAIMANT,
        reason_code="DISPUTE_REOPENED",
        details={"dispute_reason": req.disputeReason},
    )

    subclaim = SubClaim(
        sub_claim_id=f"SUB-2026-{uuid4().hex[:6].upper()}",
        parent_claim_id=claim_id,
        disputed_amount=req.supplementalAmount,
        dispute_reason=req.disputeReason,
        dispute_category=req.disputeCategory,
        status="UNDER_REVIEW",
        reopened_at=datetime.now(timezone.utc),
    )
    subclaim_repo.create_subclaim(subclaim)

    return ReopenClaimResponse(
        subClaimId=subclaim.sub_claim_id,
        parentClaimId=claim_id,
        parentClaimStatus=ClaimState.REOPENED.value,
        subClaimStatus=subclaim.status,
        disputedAmount=subclaim.disputed_amount,
        disputeReason=subclaim.dispute_reason,
        reopenedAt=subclaim.reopened_at,
    )


@router.get("/{claim_id}/linked-claims")
def get_linked_subclaims(
    claim_id: str,
    subclaim_repo: SubClaimRepository = Depends(get_subclaim_repository),
) -> list[dict[str, object]]:
    subclaims = subclaim_repo.get_by_parent_claim_id(claim_id)
    return [
        {
            "subClaimId": s.sub_claim_id,
            "parentClaimId": s.parent_claim_id,
            "disputedAmount": s.disputed_amount,
            "disputeReason": s.dispute_reason,
            "status": s.status,
            "reopenedAt": s.reopened_at,
        }
        for s in subclaims
    ]
