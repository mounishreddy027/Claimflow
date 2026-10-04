from collections.abc import Mapping
from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

from claimflow.repositories.audit_repository import AuditRepository
from claimflow.types.audit import AuditLogEntry
from claimflow.utils.pii_redaction import redact_pii


class AuditService:
    """Service orchestrating audit logging, PII sanitization, and cryptographic chaining."""

    def __init__(self, repository: AuditRepository | None = None) -> None:
        self.repository = repository if repository is not None else AuditRepository()

    def record_event(
        self,
        correlation_id: str,
        actor_id: str,
        actor_role: object,
        operation_type: object,
        claim_id: str,
        previous_state: str | None = None,
        new_state: str | None = None,
        reason_code: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> AuditLogEntry:
        """Sanitize details, compute hash, and append immutable audit event."""
        role_str = str(getattr(actor_role, "value", actor_role))
        op_str = str(getattr(operation_type, "value", operation_type))
        sanitized_details: dict[str, object] = {}
        if details:
            cleaned = redact_pii(dict(details))
            if isinstance(cleaned, dict):
                sanitized_details = cast(dict[str, object], cleaned)

        audit_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)
        prev_hash = self.repository.get_latest_hash()

        candidate = AuditLogEntry(
            audit_id=audit_id,
            correlation_id=correlation_id,
            timestamp=timestamp,
            actor_id=actor_id,
            actor_role=role_str,
            operation_type=op_str,
            claim_id=claim_id,
            previous_state=previous_state,
            new_state=new_state,
            reason_code=reason_code,
            detail_json=sanitized_details,
            previous_hash=prev_hash,
            entry_hash="",
        )
        entry_hash = candidate.calculate_hash(prev_hash)
        final_entry = AuditLogEntry(
            audit_id=candidate.audit_id,
            correlation_id=candidate.correlation_id,
            timestamp=candidate.timestamp,
            actor_id=candidate.actor_id,
            actor_role=candidate.actor_role,
            operation_type=candidate.operation_type,
            claim_id=candidate.claim_id,
            previous_state=candidate.previous_state,
            new_state=candidate.new_state,
            reason_code=candidate.reason_code,
            detail_json=candidate.detail_json,
            previous_hash=prev_hash,
            entry_hash=entry_hash,
        )
        return self.repository.append(final_entry)

    def get_claim_history(
        self, claim_id: str, limit: int = 50, offset: int = 0
    ) -> list[AuditLogEntry]:
        """Fetch chronologically sorted audit history for a claim."""
        return self.repository.get_by_claim_id(claim_id, limit=limit, offset=offset)

    def verify_integrity(self) -> bool:
        """Verify unbroken cryptographic chaining for the entire audit repository."""
        return self.repository.verify_chain_integrity()
