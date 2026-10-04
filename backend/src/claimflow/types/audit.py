import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AuditLogEntry:
    """Immutable audit trail record with SHA-256 hash chaining."""

    audit_id: str
    correlation_id: str
    timestamp: datetime
    actor_id: str
    actor_role: str
    operation_type: str
    claim_id: str
    previous_state: str | None = None
    new_state: str | None = None
    reason_code: str | None = None
    detail_json: dict[str, object] = field(default_factory=dict)
    previous_hash: str = "0" * 64
    entry_hash: str = ""

    def calculate_hash(self, prev_hash: str) -> str:
        """Compute SHA-256 hash of this audit log entry linked to prev_hash."""
        serialized_details = json.dumps(self.detail_json, sort_keys=True, default=str)
        iso_timestamp = self.timestamp.isoformat()
        payload = (
            f"{prev_hash}|{self.audit_id}|{self.correlation_id}|{iso_timestamp}|"
            f"{self.actor_id}|{self.actor_role}|{self.operation_type}|{self.claim_id}|"
            f"{self.previous_state or ''}|{self.new_state or ''}|{self.reason_code or ''}|"
            f"{serialized_details}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Convert audit log entry to serializable dictionary."""
        return {
            "audit_id": self.audit_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "operation_type": self.operation_type,
            "claim_id": self.claim_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "reason_code": self.reason_code,
            "detail_json": self.detail_json,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }
