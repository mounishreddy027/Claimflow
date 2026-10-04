from typing import Annotated

from fastapi import APIRouter, Depends, Query

from claimflow.api.dependencies import get_audit_service
from claimflow.api.schemas import AuditLogResponse
from claimflow.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit-trail", tags=["audit"])


@router.get("/{claim_id}", response_model=list[AuditLogResponse])
def get_claim_audit_trail(
    claim_id: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    audit_service: AuditService = Depends(get_audit_service),
) -> list[AuditLogResponse]:
    history = audit_service.get_claim_history(claim_id=claim_id, limit=limit, offset=offset)
    return [
        AuditLogResponse(
            audit_id=entry.audit_id,
            correlation_id=entry.correlation_id,
            timestamp=entry.timestamp.isoformat(),
            actor_id=entry.actor_id,
            actor_role=entry.actor_role,
            operation_type=entry.operation_type,
            claim_id=entry.claim_id,
            previous_state=entry.previous_state,
            new_state=entry.new_state,
            reason_code=entry.reason_code,
            detail_json=entry.detail_json,
            previous_hash=entry.previous_hash,
            entry_hash=entry.entry_hash,
        )
        for entry in history
    ]
