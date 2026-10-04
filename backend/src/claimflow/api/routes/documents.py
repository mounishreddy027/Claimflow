from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from claimflow.api.dependencies import get_claim_repository, get_document_repository
from claimflow.api.schemas import (
    ChecklistSummaryResponse,
    DocumentItemResponse,
    DocumentVerifyRequest,
    DocumentVerifyResponse,
)
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.document_repository import DocumentRepository
from claimflow.types.enums import ActorRole, ClaimState

router = APIRouter(prefix="/api/v1/claims", tags=["documents"])


@router.get("/{claim_id}/documents", response_model=ChecklistSummaryResponse)
def get_claim_documents(
    claim_id: str,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    doc_repo: DocumentRepository = Depends(get_document_repository),
) -> ChecklistSummaryResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    docs = doc_repo.get_documents_by_claim_id(claim_id)
    mandatory = doc_repo.MANDATORY_CHECKLISTS.get(claim.claim_type.value, [])
    verified_count = sum(1 for d in docs if d.status == "VERIFIED")
    is_complete = doc_repo.is_checklist_complete(claim_id, claim.claim_type)

    checklist_status = "COMPLETE" if is_complete else "INCOMPLETE"
    item_responses = [
        DocumentItemResponse(
            documentId=d.document_id,
            documentType=d.document_type,
            fileName=d.file_name,
            status=d.status,
            verifiedAt=d.verified_at,
            verifiedBy=d.verified_by,
        )
        for d in docs
    ]
    return ChecklistSummaryResponse(
        claimId=claim_id,
        claimType=claim.claim_type.value,
        checklistStatus=checklist_status,
        mandatoryCount=len(mandatory),
        verifiedCount=verified_count,
        documents=item_responses,
    )


@router.post(
    "/{claim_id}/documents/{doc_id}/verify",
    response_model=DocumentVerifyResponse,
)
def verify_claim_document(
    claim_id: str,
    doc_id: str,
    req: DocumentVerifyRequest,
    x_actor_role: Annotated[str | None, Header()] = None,
    claim_repo: ClaimRepository = Depends(get_claim_repository),
    doc_repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentVerifyResponse:
    claim = claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    verifier = "assessor_user_1"
    try:
        updated_doc = doc_repo.verify_document(
            doc_id=doc_id,
            verified_by=verifier,
            action=req.action,
            rejection_reason=req.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # If checklist is complete and claim is FILED, advance to UNDER_REVIEW
    if doc_repo.is_checklist_complete(claim_id, claim.claim_type) and claim.current_state == ClaimState.FILED:
        claim_repo.transition_claim_state(
            claim_id=claim_id,
            target_state=ClaimState.UNDER_REVIEW,
            actor_id=verifier,
            actor_role=ActorRole.ASSESSOR,
            reason_code="DOCS_VERIFIED",
        )

    return DocumentVerifyResponse(
        documentId=updated_doc.document_id,
        status=updated_doc.status,
        verifiedBy=updated_doc.verified_by or verifier,
        verifiedAt=updated_doc.verified_at or datetime.now(timezone.utc),
    )
