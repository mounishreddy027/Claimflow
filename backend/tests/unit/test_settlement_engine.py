from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from claimflow.domain.claim import Claim
from claimflow.repositories.audit_repository import AuditRepository
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.settlement_repository import SettlementRepository
from claimflow.services.assessment_engine import AssessmentEngine
from claimflow.services.audit_service import AuditService
from claimflow.services.fraud_service import FraudService
from claimflow.services.settlement_service import SettlementService
from claimflow.types.enums import (
    ActorRole,
    AdjudicationDecision,
    ClaimState,
    ClaimType,
    PayoutStatus,
)
from claimflow.types.exceptions import (
    ImmutabilityViolationError,
    PayoutInvariantViolationException,
)

pytestmark = [pytest.mark.AC_06, pytest.mark.AC_07]


@pytest.fixture
def settlement_service() -> SettlementService:
    audit_repo = AuditRepository()
    audit_service = AuditService(repository=audit_repo)
    claim_repo = ClaimRepository(audit_service=audit_service)
    settlement_repo = SettlementRepository()
    return SettlementService(
        claim_repository=claim_repo,
        settlement_repository=settlement_repo,
        assessment_engine=AssessmentEngine(),
        fraud_service=FraudService(),
        audit_service=audit_service,
    )


def test_adjudication_decision_auto_approve(settlement_service: SettlementService) -> None:
    claim = Claim(
        claim_id=f"CLM-{uuid4().hex[:6]}",
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("4000.00"),
        incident_date=date(2026, 6, 1),
        incident_description="Clean collision",
        current_state=ClaimState.UNDER_REVIEW,
    )
    policy = {
        "policy_number": "POL-MTR-1001",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("10000.00"),
        "deductible": Decimal("500.00"),
        "copay_percent": Decimal("0.00"),
        "fraud_threshold": 50,
        "version": 1,
    }

    decision_res = settlement_service.adjudicate(
        claim=claim,
        policy=policy,
        docs_verified=True,
    )
    assert decision_res.decision == AdjudicationDecision.AUTO_APPROVE
    assert decision_res.reason_code == "POL_APPR_STP_01"


def test_adjudication_decision_diverts_to_manual_review_on_fraud(
    settlement_service: SettlementService,
) -> None:
    claim = Claim(
        claim_id=f"CLM-{uuid4().hex[:6]}",
        policy_number="POL-HLT-2002",
        claim_type=ClaimType.HEALTH,
        claim_amount=Decimal("9500.00"),  # > 90% sum insured (+20)
        incident_date=date(2026, 1, 5),   # rapid inception (+25)
        incident_description="Hospitalization",
        current_state=ClaimState.UNDER_REVIEW,
    )
    policy = {
        "policy_number": "POL-HLT-2002",
        "effective_date": date(2026, 1, 1),
        "sum_insured": Decimal("10000.00"),
        "deductible": Decimal("200.00"),
        "copay_percent": Decimal("0.00"),
        "fraud_threshold": 40,
        "version": 1,
    }

    decision_res = settlement_service.adjudicate(
        claim=claim,
        policy=policy,
        docs_verified=True,
    )
    assert decision_res.decision == AdjudicationDecision.MANUAL_REVIEW
    assert decision_res.reason_code == "POL_REV_FRAUD_FLAG_01"


def test_immutable_payout_generation_and_state_transition(
    settlement_service: SettlementService,
) -> None:
    claim_id = f"CLM-{uuid4().hex[:6]}"
    claim = Claim(
        claim_id=claim_id,
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("4000.00"),
        incident_date=date(2026, 6, 1),
        incident_description="Accident",
        current_state=ClaimState.FILED,
    )
    settlement_service.claim_repository.create_claim(
        claim, actor_id="user_1", actor_role=ActorRole.CLAIMANT
    )
    settlement_service.claim_repository.transition_claim_state(
        claim_id, ClaimState.UNDER_REVIEW, actor_id="assessor", actor_role=ActorRole.ASSESSOR
    )
    settlement_service.claim_repository.transition_claim_state(
        claim_id, ClaimState.APPROVED, actor_id="assessor", actor_role=ActorRole.ASSESSOR
    )

    assessment = settlement_service.assessment_engine.assess(
        claim_id=claim_id,
        claim_amount=Decimal("4000.00"),
        sum_insured=Decimal("10000.00"),
        deductible=Decimal("500.00"),
        copay_percent=Decimal("0.00"),
        assessed_by="assessor",
    )
    assert assessment.payable_amount == Decimal("3500.00")

    payout = settlement_service.settle_claim(
        claim_id=claim_id,
        assessment=assessment,
        requested_payout=Decimal("3500.00"),
        actor_id="system_payout",
        actor_role=ActorRole.SYSTEM,
    )

    assert payout.payout_amount == Decimal("3500.00")
    assert payout.status == PayoutStatus.DISBURSED
    assert payout.claim_id == claim_id

    # Verify claim state transitioned to SETTLED
    updated_claim = settlement_service.claim_repository.get_claim(claim_id)
    assert updated_claim is not None
    assert updated_claim.current_state == ClaimState.SETTLED


def test_payout_amount_mismatch_raises_invariant_violation(
    settlement_service: SettlementService,
) -> None:
    claim_id = f"CLM-{uuid4().hex[:6]}"
    claim = Claim(
        claim_id=claim_id,
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("4000.00"),
        incident_date=date(2026, 6, 1),
        incident_description="Accident",
        current_state=ClaimState.FILED,
    )
    settlement_service.claim_repository.create_claim(
        claim, actor_id="user_1", actor_role=ActorRole.CLAIMANT
    )
    settlement_service.claim_repository.transition_claim_state(
        claim_id, ClaimState.UNDER_REVIEW, actor_id="assessor", actor_role=ActorRole.ASSESSOR
    )
    settlement_service.claim_repository.transition_claim_state(
        claim_id, ClaimState.APPROVED, actor_id="assessor", actor_role=ActorRole.ASSESSOR
    )

    assessment = settlement_service.assessment_engine.assess(
        claim_id=claim_id,
        claim_amount=Decimal("4000.00"),
        sum_insured=Decimal("10000.00"),
        deductible=Decimal("500.00"),
        copay_percent=Decimal("0.00"),
        assessed_by="assessor",
    )

    # Requested payout $3,700 vs assessed $3,500
    with pytest.raises(PayoutInvariantViolationException):
        settlement_service.settle_claim(
            claim_id=claim_id,
            assessment=assessment,
            requested_payout=Decimal("3700.00"),
            actor_id="payout_engine",
            actor_role=ActorRole.SYSTEM,
        )


def test_payout_repository_immutability(settlement_service: SettlementService) -> None:
    repo = settlement_service.settlement_repository
    with pytest.raises(ImmutabilityViolationError):
        repo.update("PAY-1", {"payout_amount": Decimal("9999.00")})

    with pytest.raises(ImmutabilityViolationError):
        repo.delete("PAY-1")
