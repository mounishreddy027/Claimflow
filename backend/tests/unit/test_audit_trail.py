from datetime import datetime, timezone
from uuid import uuid4

import pytest

from claimflow.repositories.audit_repository import AuditRepository
from claimflow.services.audit_service import AuditService
from claimflow.types.enums import ActorRole, OperationType
from claimflow.types.exceptions import AuditIntegrityError, ImmutabilityViolationError
from claimflow.utils.pii_redaction import redact_pii


def test_pii_redaction_utility() -> None:
    raw_data: dict[str, object] = {
        "claimant_name": "John Doe",
        "ssn": "123-45-6789",
        "bank_account": "987654321",
        "credit_card": "4111222233334444",
        "nested": {
            "password": "secret_pass",
            "file_content_stub": "base64_data",
            "public_info": "safe_value",
        },
    }
    redacted = redact_pii(raw_data)
    assert isinstance(redacted, dict)
    assert redacted["ssn"] == "[REDACTED]"
    assert redacted["bank_account"] == "[REDACTED]"
    assert redacted["credit_card"] == "[REDACTED]"
    assert redacted["claimant_name"] == "John Doe"
    nested = redacted["nested"]
    assert isinstance(nested, dict)
    assert nested["password"] == "[REDACTED]"
    assert nested["file_content_stub"] == "[REDACTED]"
    assert nested["public_info"] == "safe_value"


def test_record_audit_event() -> None:
    repo = AuditRepository()
    service = AuditService(repository=repo)
    correlation_id = str(uuid4())
    claim_id = "CLM-2026-0001"

    entry = service.record_event(
        correlation_id=correlation_id,
        actor_id="user_123",
        actor_role=ActorRole.CLAIMANT,
        operation_type=OperationType.CLAIM_CREATED,
        claim_id=claim_id,
        previous_state=None,
        new_state="FILED",
        reason_code="FNOL_SUBMITTED",
        details={"incident_type": "COLLISION", "ssn": "000-11-2222"},
    )

    assert entry.audit_id is not None
    assert entry.correlation_id == correlation_id
    assert entry.claim_id == claim_id
    assert entry.actor_id == "user_123"
    assert entry.actor_role == ActorRole.CLAIMANT.value
    assert entry.operation_type == OperationType.CLAIM_CREATED.value
    assert entry.previous_state is None
    assert entry.new_state == "FILED"
    assert entry.reason_code == "FNOL_SUBMITTED"
    assert entry.detail_json["ssn"] == "[REDACTED]"
    assert entry.detail_json["incident_type"] == "COLLISION"
    assert entry.timestamp.tzinfo == timezone.utc
    assert len(entry.entry_hash) == 64
    assert entry.previous_hash == "0" * 64


def test_hash_chaining_and_integrity_verification() -> None:
    repo = AuditRepository()
    service = AuditService(repository=repo)
    claim_id = "CLM-2026-0002"

    e1 = service.record_event(
        correlation_id=str(uuid4()),
        actor_id="user_1",
        actor_role=ActorRole.CLAIMANT,
        operation_type=OperationType.CLAIM_CREATED,
        claim_id=claim_id,
        previous_state=None,
        new_state="FILED",
    )

    e2 = service.record_event(
        correlation_id=str(uuid4()),
        actor_id="assessor_1",
        actor_role=ActorRole.ASSESSOR,
        operation_type=OperationType.STATE_TRANSITION,
        claim_id=claim_id,
        previous_state="FILED",
        new_state="UNDER_REVIEW",
    )

    e3 = service.record_event(
        correlation_id=str(uuid4()),
        actor_id="assessor_1",
        actor_role=ActorRole.ASSESSOR,
        operation_type=OperationType.STATE_TRANSITION,
        claim_id=claim_id,
        previous_state="UNDER_REVIEW",
        new_state="APPROVED",
    )

    assert e1.previous_hash == "0" * 64
    assert e2.previous_hash == e1.entry_hash
    assert e3.previous_hash == e2.entry_hash
    assert repo.verify_chain_integrity() is True


def test_hash_chain_tamper_detection() -> None:
    repo = AuditRepository()
    service = AuditService(repository=repo)
    claim_id = "CLM-2026-0003"

    service.record_event(
        correlation_id=str(uuid4()),
        actor_id="user_1",
        actor_role=ActorRole.CLAIMANT,
        operation_type=OperationType.CLAIM_CREATED,
        claim_id=claim_id,
    )
    service.record_event(
        correlation_id=str(uuid4()),
        actor_id="assessor_1",
        actor_role=ActorRole.ASSESSOR,
        operation_type=OperationType.STATE_TRANSITION,
        claim_id=claim_id,
        previous_state="FILED",
        new_state="UNDER_REVIEW",
    )

    # Tamper with an entry in the repository storage
    tampered_entry = repo.get_all()[0]
    tampered_entry_corrupted = tampered_entry.__class__(
        audit_id=tampered_entry.audit_id,
        correlation_id=tampered_entry.correlation_id,
        timestamp=tampered_entry.timestamp,
        actor_id="hacker_999",
        actor_role=tampered_entry.actor_role,
        operation_type=tampered_entry.operation_type,
        claim_id=tampered_entry.claim_id,
        previous_state=tampered_entry.previous_state,
        new_state=tampered_entry.new_state,
        reason_code=tampered_entry.reason_code,
        detail_json=tampered_entry.detail_json,
        previous_hash=tampered_entry.previous_hash,
        entry_hash=tampered_entry.entry_hash,
    )
    repo._storage[0] = tampered_entry_corrupted

    with pytest.raises(AuditIntegrityError):
        repo.verify_chain_integrity()


def test_immutability_constraints() -> None:
    repo = AuditRepository()
    service = AuditService(repository=repo)
    entry = service.record_event(
        correlation_id=str(uuid4()),
        actor_id="user_1",
        actor_role=ActorRole.SYSTEM,
        operation_type=OperationType.CLAIM_CREATED,
        claim_id="CLM-IMMUTABLE-1",
    )

    with pytest.raises(ImmutabilityViolationError):
        repo.update(entry.audit_id, {"actor_id": "modified"})

    with pytest.raises(ImmutabilityViolationError):
        repo.delete(entry.audit_id)


def test_queries_filtering_and_pagination() -> None:
    repo = AuditRepository()
    service = AuditService(repository=repo)
    claim_a = "CLM-A"
    claim_b = "CLM-B"

    service.record_event(
        correlation_id="corr-1",
        actor_id="user_1",
        actor_role=ActorRole.CLAIMANT,
        operation_type=OperationType.CLAIM_CREATED,
        claim_id=claim_a,
    )
    service.record_event(
        correlation_id="corr-2",
        actor_id="admin_1",
        actor_role=ActorRole.ADMIN,
        operation_type=OperationType.OVERRIDE_APPLIED,
        claim_id=claim_a,
    )
    service.record_event(
        correlation_id="corr-3",
        actor_id="user_2",
        actor_role=ActorRole.CLAIMANT,
        operation_type=OperationType.CLAIM_CREATED,
        claim_id=claim_b,
    )

    history_a = service.get_claim_history(claim_id=claim_a)
    assert len(history_a) == 2
    assert history_a[0].operation_type == OperationType.CLAIM_CREATED.value
    assert history_a[1].operation_type == OperationType.OVERRIDE_APPLIED.value

    # Test filtering by actor_id
    filtered_admin = repo.query(actor_id="admin_1")
    assert len(filtered_admin) == 1
    assert filtered_admin[0].actor_id == "admin_1"

    # Test filtering by operation_type
    filtered_created = repo.query(operation_type=OperationType.CLAIM_CREATED.value)
    assert len(filtered_created) == 2

    # Test filtering by timestamp
    entry_a = repo.get_all()[0]
    time_filtered = repo.query(
        start_time=datetime(2020, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    assert len(time_filtered) == 3

    # Test get_by_id
    found = repo.get_by_id(entry_a.audit_id)
    assert found is not None
    assert found.audit_id == entry_a.audit_id
    assert repo.get_by_id("non-existent-id") is None

    # Test to_dict
    dict_repr = entry_a.to_dict()
    assert dict_repr["audit_id"] == entry_a.audit_id
    assert dict_repr["entry_hash"] == entry_a.entry_hash

    # Test pagination
    page1 = service.get_claim_history(claim_id=claim_a, limit=1, offset=0)
    assert len(page1) == 1
    page2 = service.get_claim_history(claim_id=claim_a, limit=1, offset=1)
    assert len(page2) == 1
    assert page1[0].audit_id != page2[0].audit_id

