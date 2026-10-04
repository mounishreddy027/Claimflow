from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from uuid import uuid4

from claimflow.domain.claim import Claim, StateTransitionRecord
from claimflow.domain.state_machine import ClaimStateMachine
from claimflow.services.audit_service import AuditService
from claimflow.types.enums import ClaimState, OperationType


class ClaimRepository:
    """Repository managing claim entities, state machine transitions, and audit trails."""

    def __init__(
        self,
        audit_service: AuditService | None = None,
        state_machine: ClaimStateMachine | None = None,
    ) -> None:
        self.audit_service = audit_service if audit_service is not None else AuditService()
        self.state_machine = state_machine if state_machine is not None else ClaimStateMachine()
        self._storage: dict[str, Claim] = {}

    def create_claim(self, claim: Claim, actor_id: str, actor_role: object) -> Claim:
        """Create and store a new claim aggregate, initializing its state and audit record."""
        self.state_machine.validate_transition(
            claim.claim_id,
            None,
            claim.current_state,
            actor_role=actor_role,
        )
        role_str = str(getattr(actor_role, "value", actor_role))
        now = datetime.now(timezone.utc)
        init_transition = StateTransitionRecord(
            transition_id=str(uuid4()),
            claim_id=claim.claim_id,
            from_state=None,
            to_state=claim.current_state.value,
            actor_id=actor_id,
            actor_role=role_str,
            timestamp=now,
            reason_code=claim.reason_code,
        )
        claim.transitions.append(init_transition)
        self._storage[claim.claim_id] = claim

        self.audit_service.record_event(
            correlation_id=str(uuid4()),
            actor_id=actor_id,
            actor_role=actor_role,
            operation_type=OperationType.CLAIM_CREATED,
            claim_id=claim.claim_id,
            previous_state=None,
            new_state=claim.current_state.value,
            reason_code=claim.reason_code,
            details={
                "policy_number": claim.policy_number,
                "claim_type": claim.claim_type.value,
                "claim_amount": str(claim.claim_amount),
            },
        )
        return claim

    def get_claim(self, claim_id: str) -> Claim | None:
        """Fetch claim by ID."""
        return self._storage.get(claim_id)

    def list_claims(self) -> list[Claim]:
        """Return all claims in storage."""
        return list(self._storage.values())

    def transition_claim_state(
        self,
        claim_id: str,
        target_state: ClaimState,
        actor_id: str,
        actor_role: object,
        reason_code: str | None = None,
        details: Mapping[str, object] | None = None,
        guard: Callable[[], bool] | None = None,
        guard_failure_message: str = "Transition guard condition failed",
    ) -> Claim:
        """
        Transition claim state through state machine guards, recording transition history and audit.

        Raises:
            KeyError: If claim does not exist.
            ValueError: If a business guard check fails.
            InvalidClaimStateException: If the transition path is not permitted.
        """
        claim = self._storage.get(claim_id)
        if claim is None:
            raise KeyError(f"Claim not found: {claim_id}")

        if guard is not None and not guard():
            raise ValueError(guard_failure_message)

        self.state_machine.validate_transition(
            claim_id=claim_id,
            current_state=claim.current_state,
            target_state=target_state,
            actor_role=actor_role,
        )

        role_str = str(getattr(actor_role, "value", actor_role))
        now = datetime.now(timezone.utc)
        prev_state = claim.current_state.value

        transition_record = StateTransitionRecord(
            transition_id=str(uuid4()),
            claim_id=claim_id,
            from_state=prev_state,
            to_state=target_state.value,
            actor_id=actor_id,
            actor_role=role_str,
            timestamp=now,
            reason_code=reason_code,
        )
        claim.transitions.append(transition_record)
        claim.current_state = target_state
        claim.reason_code = reason_code
        claim.updated_at = now

        op_type = (
            OperationType.OVERRIDE_APPLIED
            if role_str in {"ADMIN", "ROLE_ADMIN"}
            and prev_state in {ClaimState.APPROVED.value, ClaimState.REJECTED.value}
            else OperationType.STATE_TRANSITION
        )

        self.audit_service.record_event(
            correlation_id=str(uuid4()),
            actor_id=actor_id,
            actor_role=actor_role,
            operation_type=op_type,
            claim_id=claim_id,
            previous_state=prev_state,
            new_state=target_state.value,
            reason_code=reason_code,
            details=details,
        )
        return claim
