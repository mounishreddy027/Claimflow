from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status

from claimflow.api.dependencies import get_claim_repository
from claimflow.api.schemas import AdminOverrideRequest, AdminOverrideResponse
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.types.enums import ActorRole, ClaimState
from claimflow.types.exceptions import InvalidClaimStateException

router = APIRouter(prefix="/api/v1/admin/claims", tags=["admin"])


@router.post("/{claim_id}/override", response_model=AdminOverrideResponse)
def override_adjudication_decision(
    claim_id: str,
    req: AdminOverrideRequest,
    x_actor_role: Annotated[str | None, Header()] = None,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
) -> AdminOverrideResponse:
    if x_actor_role not in {"ADMIN", "ROLE_ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative overrides require ROLE_ADMIN authority",
        )

    if not req.comment.strip() or not req.reasonCode.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Justification comment and reason code are mandatory for administrative overrides.",
        )

    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    prev_state = claim.current_state.value
    dec_upper = req.newDecision.upper()
    if dec_upper in {"REJECT", "REJECTED"}:
        target_state = ClaimState.REJECTED
    elif dec_upper in {"APPROVE", "APPROVED"}:
        target_state = ClaimState.APPROVED
    else:
        target_state = ClaimState(req.newDecision)

    try:
        claim_repo.transition_claim_state(
            claim_id=claim_id,
            target_state=target_state,
            actor_id="admin_sarah",
            actor_role=ActorRole.ADMIN,
            reason_code=req.reasonCode,
            details={"comment": req.comment, "previousDecision": prev_state},
        )
    except InvalidClaimStateException as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return AdminOverrideResponse(
        overrideId=f"OVR-{uuid4().hex[:8].upper()}",
        claimId=claim_id,
        previousDecision=prev_state,
        newDecision=req.newDecision,
        reasonCode=req.reasonCode,
        comment=req.comment,
        actorId="admin_sarah",
        timestamp=datetime.now(timezone.utc),
    )
