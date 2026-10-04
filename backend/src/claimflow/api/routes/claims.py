from datetime import date
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status

from claimflow.api.dependencies import (
    get_claim_repository,
    get_document_repository,
    get_policy_repository,
    get_policy_service,
)
from claimflow.api.schemas import (
    ClaimDetailResponse,
    ClaimIntakeRequest,
    ClaimIntakeResponse,
    DocumentReceiptResponse,
    StateTransitionResponse,
)
from claimflow.domain.claim import Claim
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.document_repository import DocumentRepository
from claimflow.repositories.policy_repository import PolicyRepository
from claimflow.services.policy_service import PolicyService
from claimflow.types.enums import ActorRole, ClaimState
from claimflow.types.exceptions import PolicyNotActiveException, PolicyNotFoundError

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])


def _validate_policy(
    policy_repo: PolicyRepository,
    policy_service: PolicyService,
    req: ClaimIntakeRequest,
) -> None:
    policy = policy_repo.get_policy(req.policyNumber)
    if policy is None:
        raise PolicyNotFoundError(req.policyNumber)

    effective = cast(date, policy["effective_date"])
    expiry = cast(date | None, policy.get("expiry_date"))
    pol_status = str(policy.get("status", "ACTIVE"))

    if pol_status != "ACTIVE":
        raise PolicyNotActiveException(
            policy_number=req.policyNumber,
            incident_date=req.incidentDate,
            effective_date=effective,
            expiry_date=expiry,
            reason_code=pol_status,
        )

    policy_service.validate_active(policy, req.incidentDate)


@router.post("/intake", response_model=ClaimIntakeResponse, status_code=status.HTTP_201_CREATED)
def submit_fnol(
    req: ClaimIntakeRequest,
    x_correlation_id: Annotated[str | None, Header()] = None,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    policy_repo: PolicyRepository = Depends(get_policy_repository),
    policy_service: PolicyService = Depends(get_policy_service),
    doc_repo: DocumentRepository = Depends(get_document_repository),
) -> ClaimIntakeResponse:
    _validate_policy(policy_repo, policy_service, req)
    claim_id = f"CLM-2026-{uuid4().hex[:5].upper()}"
    claim = Claim(
        claim_id=claim_id,
        policy_number=req.policyNumber,
        claim_type=req.claimType,
        claim_amount=req.claimAmount,
        incident_date=req.incidentDate,
        incident_description=req.incidentDescription,
        current_state=ClaimState.FILED,
    )
    saved_claim = claim_repo.create_claim(claim, actor_id="customer_portal", actor_role=ActorRole.CLAIMANT)

    receipts: list[DocumentReceiptResponse] = []
    for doc in req.supportingDocuments:
        rec = doc_repo.add_document(claim_id=claim_id, document_type=doc.documentType, file_name=doc.fileName)
        receipts.append(DocumentReceiptResponse(documentId=rec.document_id, documentType=rec.document_type, status=rec.status))

    return ClaimIntakeResponse(
        claimId=saved_claim.claim_id,
        policyNumber=saved_claim.policy_number,
        claimType=saved_claim.claim_type.value,
        status=saved_claim.current_state.value,
        claimAmount=saved_claim.claim_amount,
        incidentDate=saved_claim.incident_date,
        documentReceipts=receipts,
        createdAt=saved_claim.created_at,
    )


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
def get_claim_details(
    claim_id: str,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
) -> ClaimDetailResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    transitions = [
        StateTransitionResponse(
            transitionId=t.transition_id,
            fromState=t.from_state,
            toState=t.to_state,
            actorId=t.actor_id,
            actorRole=t.actor_role,
            reasonCode=t.reason_code,
            timestamp=t.timestamp,
        )
        for t in claim.transitions
    ]
    return ClaimDetailResponse(
        claimId=claim.claim_id,
        policyNumber=claim.policy_number,
        claimType=claim.claim_type.value,
        status=claim.current_state.value,
        claimAmount=claim.claim_amount,
        incidentDate=claim.incident_date,
        incidentDescription=claim.incident_description,
        transitions=transitions,
        createdAt=claim.created_at,
        updatedAt=claim.updated_at,
    )
