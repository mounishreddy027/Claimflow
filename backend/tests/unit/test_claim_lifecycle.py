from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from claimflow.domain.claim import Claim
from claimflow.repositories.audit_repository import AuditRepository
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.services.audit_service import AuditService
from claimflow.types.enums import ActorRole, ClaimState, ClaimType, OperationType

pytestmark = pytest.mark.AC_10


@pytest.fixture
def claim_repo() -> ClaimRepository:
    audit_repo = AuditRepository()
    audit_service = AuditService(repository=audit_repo)
    return ClaimRepository(audit_service=audit_service)


def test_claim_creation_initializes_filed_and_audits(claim_repo: ClaimRepository) -> None:
    claim_id = f"CLM-{uuid4().hex[:8]}"
    claim = Claim(
        claim_id=claim_id,
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("3500.00"),
        incident_date=date(2026, 9, 15),
        incident_description="Front bumper collision",
        current_state=ClaimState.FILED,
    )

    saved = claim_repo.create_claim(claim, actor_id="user_1", actor_role=ActorRole.CLAIMANT)
    assert saved.claim_id == claim_id
    assert saved.current_state == ClaimState.FILED
    assert len(saved.transitions) == 1
    assert saved.transitions[0].to_state == ClaimState.FILED.value

    # Verify automatic audit record
    audit_history = claim_repo.audit_service.get_claim_history(claim_id)
    assert len(audit_history) == 1
    assert audit_history[0].operation_type == OperationType.CLAIM_CREATED.value
    assert audit_history[0].new_state == ClaimState.FILED.value


def test_transition_under_review_with_guard(claim_repo: ClaimRepository) -> None:
    claim_id = f"CLM-{uuid4().hex[:8]}"
    claim = Claim(
        claim_id=claim_id,
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("3500.00"),
        incident_date=date(2026, 9, 15),
        incident_description="Front bumper collision",
        current_state=ClaimState.FILED,
    )
    claim_repo.create_claim(claim, actor_id="user_1", actor_role=ActorRole.CLAIMANT)

    # Failed guard blocks transition
    with pytest.raises(ValueError, match="Checklist incomplete"):
        claim_repo.transition_claim_state(
            claim_id=claim_id,
            target_state=ClaimState.UNDER_REVIEW,
            actor_id="assessor_1",
            actor_role=ActorRole.ASSESSOR,
            guard=lambda: False,
            guard_failure_message="Checklist incomplete",
        )

    # Passing guard succeeds
    updated = claim_repo.transition_claim_state(
        claim_id=claim_id,
        target_state=ClaimState.UNDER_REVIEW,
        actor_id="assessor_1",
        actor_role=ActorRole.ASSESSOR,
        guard=lambda: True,
        reason_code="DOCS_VERIFIED",
    )
    assert updated.current_state == ClaimState.UNDER_REVIEW
    assert len(updated.transitions) == 2


def test_full_lifecycle_and_transition_audit_chain(claim_repo: ClaimRepository) -> None:
    claim_id = f"CLM-{uuid4().hex[:8]}"
    claim = Claim(
        claim_id=claim_id,
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("3500.00"),
        incident_date=date(2026, 9, 15),
        incident_description="Front bumper collision",
        current_state=ClaimState.FILED,
    )
    claim_repo.create_claim(claim, actor_id="user_1", actor_role=ActorRole.CLAIMANT)

    # FILED -> UNDER_REVIEW
    claim_repo.transition_claim_state(
        claim_id=claim_id,
        target_state=ClaimState.UNDER_REVIEW,
        actor_id="system",
        actor_role=ActorRole.SYSTEM,
        reason_code="DOCS_VERIFIED",
    )

    # UNDER_REVIEW -> APPROVED
    claim_repo.transition_claim_state(
        claim_id=claim_id,
        target_state=ClaimState.APPROVED,
        actor_id="assessor_1",
        actor_role=ActorRole.ASSESSOR,
        reason_code="POL_APPR_STP_01",
    )

    # APPROVED -> SETTLED
    claim_repo.transition_claim_state(
        claim_id=claim_id,
        target_state=ClaimState.SETTLED,
        actor_id="system_payout",
        actor_role=ActorRole.SYSTEM,
        reason_code="PAYOUT_DISBURSED",
    )

    # SETTLED -> REOPENED
    final = claim_repo.transition_claim_state(
        claim_id=claim_id,
        target_state=ClaimState.REOPENED,
        actor_id="user_1",
        actor_role=ActorRole.CLAIMANT,
        reason_code="DISPUTE_RAISED",
    )

    assert final.current_state == ClaimState.REOPENED
    assert len(final.transitions) == 5

    # Check that audit log has all 5 entries cryptographically chained
    audit_history = claim_repo.audit_service.get_claim_history(claim_id)
    assert len(audit_history) == 5
    assert claim_repo.audit_service.verify_integrity() is True
