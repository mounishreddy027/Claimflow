from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from claimflow.domain.claim import Claim
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.settlement_repository import PayoutRecord, SettlementRepository
from claimflow.services.assessment_engine import Assessment, AssessmentEngine
from claimflow.services.audit_service import AuditService
from claimflow.services.fraud_service import FraudScreeningResult, FraudService
from claimflow.types.enums import (
    AdjudicationDecision,
    ClaimState,
    OperationType,
    PayoutStatus,
)
from claimflow.types.exceptions import PayoutInvariantViolationException
from claimflow.utils.financial import to_decimal


@dataclass(frozen=True)
class AdjudicationResult:
    """Decisioning engine adjudication result (AC-06)."""

    decision: AdjudicationDecision
    reason_code: str
    fraud_result: FraudScreeningResult
    assessment: Assessment


class SettlementService:
    """Adjudication decisioning and financial settlement execution engine (AC-06, AC-07)."""

    def __init__(
        self,
        claim_repository: ClaimRepository,
        settlement_repository: SettlementRepository,
        assessment_engine: AssessmentEngine,
        fraud_service: FraudService,
        audit_service: AuditService,
    ) -> None:
        self.claim_repository = claim_repository
        self.settlement_repository = settlement_repository
        self.assessment_engine = assessment_engine
        self.fraud_service = fraud_service
        self.audit_service = audit_service

    def adjudicate(
        self,
        claim: Claim,
        policy: Mapping[str, object],
        docs_verified: bool,
        prior_claims_count: int = 0,
    ) -> AdjudicationResult:
        """Evaluate claim for straight-through approval, manual review, or rejection."""
        fraud_res = self.fraud_service.evaluate_fraud(
            claim=claim,
            policy=policy,
            prior_claims_count=prior_claims_count,
        )
        assessment = self.assessment_engine.assess(
            claim_id=claim.claim_id,
            claim_amount=claim.claim_amount,
            sum_insured=to_decimal(policy["sum_insured"]),
            deductible=to_decimal(policy.get("deductible", Decimal("0.00"))),
            copay_percent=to_decimal(policy.get("copay_percent", Decimal("0.00"))),
        )

        if not docs_verified:
            return AdjudicationResult(
                decision=AdjudicationDecision.MANUAL_REVIEW,
                reason_code="POL_REV_DOC_ANOMALY_02",
                fraud_result=fraud_res,
                assessment=assessment,
            )

        if fraud_res.is_flagged:
            return AdjudicationResult(
                decision=AdjudicationDecision.MANUAL_REVIEW,
                reason_code="POL_REV_FRAUD_FLAG_01",
                fraud_result=fraud_res,
                assessment=assessment,
            )

        if assessment.payable_amount <= Decimal("0.00"):
            return AdjudicationResult(
                decision=AdjudicationDecision.REJECT,
                reason_code="POL_REJ_ZERO_PAYABLE_03",
                fraud_result=fraud_res,
                assessment=assessment,
            )

        return AdjudicationResult(
            decision=AdjudicationDecision.AUTO_APPROVE,
            reason_code="POL_APPR_STP_01",
            fraud_result=fraud_res,
            assessment=assessment,
        )

    def settle_claim(
        self,
        claim_id: str,
        assessment: Assessment,
        requested_payout: Decimal,
        actor_id: str,
        actor_role: object,
        recipient_account: str | None = None,
    ) -> PayoutRecord:
        """Disburse settlement payout ensuring exact equality to assessed payable amount."""
        req_dec = to_decimal(requested_payout)
        if req_dec != assessment.payable_amount:
            raise PayoutInvariantViolationException(
                f"Payout amount {req_dec} does not match assessed payable amount "
                f"{assessment.payable_amount} for claim {claim_id}"
            )

        # Advance claim state to SETTLED
        self.claim_repository.transition_claim_state(
            claim_id=claim_id,
            target_state=ClaimState.SETTLED,
            actor_id=actor_id,
            actor_role=actor_role,
            reason_code="PAYOUT_DISBURSED",
        )

        payout = PayoutRecord(
            payout_id=f"PAY-{uuid4().hex[:8].upper()}",
            claim_id=claim_id,
            payout_amount=assessment.payable_amount,
            currency="USD",
            status=PayoutStatus.DISBURSED,
            disbursement_rail="STUBBED_ACH",
            recipient_masked_account=recipient_account or "XXXX-XXXX-1926",
            settled_at=datetime.now(timezone.utc),
        )
        self.settlement_repository.append(payout)

        self.audit_service.record_event(
            correlation_id=str(uuid4()),
            actor_id=actor_id,
            actor_role=actor_role,
            operation_type=OperationType.SETTLEMENT_CONFIRMED,
            claim_id=claim_id,
            previous_state=ClaimState.APPROVED.value,
            new_state=ClaimState.SETTLED.value,
            reason_code="PAYOUT_DISBURSED",
            details={
                "payout_id": payout.payout_id,
                "payout_amount": str(payout.payout_amount),
            },
        )
        return payout
