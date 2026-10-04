from collections.abc import Mapping
from datetime import datetime

from claimflow.types.audit import AuditLogEntry
from claimflow.types.exceptions import AuditIntegrityError, ImmutabilityViolationError

GENESIS_HASH: str = "0" * 64


class AuditRepository:
    """Append-only audit trail repository with immutability guarantees and hash chaining."""

    def __init__(self) -> None:
        self._storage: list[AuditLogEntry] = []

    def get_latest_hash(self) -> str:
        """Return the entry_hash of the most recent audit entry, or genesis hash if empty."""
        if not self._storage:
            return GENESIS_HASH
        return self._storage[-1].entry_hash

    def append(self, entry: AuditLogEntry) -> AuditLogEntry:
        """
        Append an immutable audit entry ensuring cryptographic hash chain continuity.

        Raises:
            AuditIntegrityError: If entry hash or previous hash does not match chain.
        """
        expected_prev = self.get_latest_hash()
        if entry.previous_hash != expected_prev:
            raise AuditIntegrityError(
                f"Previous hash mismatch. Expected {expected_prev}, got {entry.previous_hash}"
            )

        computed = entry.calculate_hash(entry.previous_hash)
        if entry.entry_hash != computed:
            raise AuditIntegrityError(
                f"Entry hash mismatch. Computed {computed}, got {entry.entry_hash}"
            )

        self._storage.append(entry)
        return entry

    def get_by_id(self, audit_id: str) -> AuditLogEntry | None:
        """Fetch audit entry by its primary key ID."""
        for entry in self._storage:
            if entry.audit_id == audit_id:
                return entry
        return None

    def get_all(self) -> list[AuditLogEntry]:
        """Return all audit entries in chronological order."""
        return list(self._storage)

    def get_by_claim_id(
        self, claim_id: str, limit: int = 50, offset: int = 0
    ) -> list[AuditLogEntry]:
        """Retrieve paginated audit history for a claim, sorted by timestamp ascending."""
        matched = [e for e in self._storage if e.claim_id == claim_id]
        sorted_matched = sorted(matched, key=lambda e: e.timestamp)
        return sorted_matched[offset : offset + limit]

    def query(
        self,
        claim_id: str | None = None,
        actor_id: str | None = None,
        operation_type: str | None = None,
        correlation_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditLogEntry]:
        """Query audit log entries with multi-attribute filtering."""
        results: list[AuditLogEntry] = []
        for entry in self._storage:
            if claim_id is not None and entry.claim_id != claim_id:
                continue
            if actor_id is not None and entry.actor_id != actor_id:
                continue
            if operation_type is not None and entry.operation_type != operation_type:
                continue
            if correlation_id is not None and entry.correlation_id != correlation_id:
                continue
            if start_time is not None and entry.timestamp < start_time:
                continue
            if end_time is not None and entry.timestamp > end_time:
                continue
            results.append(entry)
        return sorted(results, key=lambda e: e.timestamp)

    def update(self, audit_id: str, updates: Mapping[str, object]) -> None:
        """Blocked by design: Audit records cannot be modified."""
        raise ImmutabilityViolationError(
            f"AuditLog records are immutable. Update rejected for audit_id {audit_id}"
        )

    def delete(self, audit_id: str) -> None:
        """Blocked by design: Audit records cannot be deleted."""
        raise ImmutabilityViolationError(
            f"AuditLog records are immutable. Deletion rejected for audit_id {audit_id}"
        )

    def verify_chain_integrity(self) -> bool:
        """
        Traverse all audit entries and verify cryptographic hash chain integrity.

        Raises:
            AuditIntegrityError: If any link in the chain is broken or tampered.
        """
        expected_prev = GENESIS_HASH
        for idx, entry in enumerate(self._storage):
            if entry.previous_hash != expected_prev:
                raise AuditIntegrityError(
                    f"Chain broken at index {idx}: expected previous hash {expected_prev}, "
                    f"got {entry.previous_hash}"
                )
            computed = entry.calculate_hash(entry.previous_hash)
            if entry.entry_hash != computed:
                raise AuditIntegrityError(
                    f"Tamper detected at index {idx} ({entry.audit_id}): computed {computed}, "
                    f"got {entry.entry_hash}"
                )
            expected_prev = entry.entry_hash
        return True
