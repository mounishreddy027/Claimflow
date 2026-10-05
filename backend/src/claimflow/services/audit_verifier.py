import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from claimflow.types.audit import AuditLogEntry


@dataclass(frozen=True)
class ChainVerificationReport:
    """Cryptographic audit chain verification result."""

    certificate_id: str
    is_valid: bool
    total_blocks_verified: int
    genesis_hash: str
    tip_hash: str
    tampered_entry_id: str | None = None
    violation_detail: str | None = None
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditVerifier:
    """
    Independent cryptographic auditor verifying hash-chained immutable WORM audit logs.
    Verifies that every entry satisfies:
    entry_hash == SHA256(previous_hash + audit_id + claim_id + operation_type + canonical_payload)
    """

    GENESIS_PREV_HASH = "0" * 64

    def verify_ledger(self, entries: Sequence[AuditLogEntry]) -> ChainVerificationReport:
        """
        Walk audit entries in chronological sequence and verify SHA-256 chain integrity.
        Raises no exceptions; returns a detailed ChainVerificationReport.
        """
        cert_id = f"CERT-{uuid4().hex[:8].upper()}"

        if not entries:
            return ChainVerificationReport(
                certificate_id=cert_id,
                is_valid=True,
                total_blocks_verified=0,
                genesis_hash=self.GENESIS_PREV_HASH,
                tip_hash=self.GENESIS_PREV_HASH,
                verified_at=datetime.now(timezone.utc),
            )

        expected_prev_hash = self.GENESIS_PREV_HASH

        for idx, entry in enumerate(entries):
            # 1. Verify previous hash link
            if entry.previous_hash != expected_prev_hash:
                return ChainVerificationReport(
                    certificate_id=cert_id,
                    is_valid=False,
                    total_blocks_verified=idx,
                    genesis_hash=entries[0].previous_hash,
                    tip_hash=entries[-1].entry_hash,
                    tampered_entry_id=entry.audit_id,
                    violation_detail=(
                        f"Previous hash broken at index {idx}. Expected {expected_prev_hash}, "
                        f"found {entry.previous_hash}"
                    ),
                    verified_at=datetime.now(timezone.utc),
                )

            # 2. Recompute current entry hash
            canonical_details = json.dumps(entry.detail_json, sort_keys=True, separators=(",", ":"))
            payload = (
                f"{entry.previous_hash}:"
                f"{entry.audit_id}:"
                f"{entry.claim_id}:"
                f"{entry.operation_type}:"
                f"{canonical_details}"
            )
            recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            if recomputed != entry.entry_hash:
                return ChainVerificationReport(
                    certificate_id=cert_id,
                    is_valid=False,
                    total_blocks_verified=idx,
                    genesis_hash=entries[0].previous_hash,
                    tip_hash=entries[-1].entry_hash,
                    tampered_entry_id=entry.audit_id,
                    violation_detail=(
                        f"Payload tampering detected at index {idx} ({entry.audit_id}). "
                        f"Stored hash: {entry.entry_hash}, Recomputed: {recomputed}"
                    ),
                    verified_at=datetime.now(timezone.utc),
                )

            expected_prev_hash = entry.entry_hash

        return ChainVerificationReport(
            certificate_id=cert_id,
            is_valid=True,
            total_blocks_verified=len(entries),
            genesis_hash=entries[0].previous_hash,
            tip_hash=entries[-1].entry_hash,
            verified_at=datetime.now(timezone.utc),
        )
