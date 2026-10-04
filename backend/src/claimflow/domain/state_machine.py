
from typing import ClassVar

from claimflow.types.enums import ActorRole, ClaimState
from claimflow.types.exceptions import InvalidClaimStateException


class ClaimStateMachine:
    """
    Finite state machine orchestrator for claim lifecycle (AC-10).

    Enforces strict transitions:
    FILED -> UNDER_REVIEW -> APPROVED / REJECTED -> SETTLED -> REOPENED
    With administrative overrides between APPROVED and REJECTED.
    """

    ADMIN_ROLES: ClassVar[set[str]] = {ActorRole.ADMIN.value, "ADMIN", "ROLE_ADMIN"}

    STANDARD_TRANSITIONS: ClassVar[dict[ClaimState | None, list[ClaimState]]] = {
        None: [ClaimState.FILED],
        ClaimState.FILED: [ClaimState.UNDER_REVIEW],
        ClaimState.UNDER_REVIEW: [ClaimState.APPROVED, ClaimState.REJECTED],
        ClaimState.APPROVED: [ClaimState.SETTLED],
        ClaimState.REJECTED: [],
        ClaimState.SETTLED: [ClaimState.REOPENED],
        ClaimState.REOPENED: [],
    }

    OVERRIDE_TRANSITIONS: ClassVar[dict[ClaimState, list[ClaimState]]] = {
        ClaimState.APPROVED: [ClaimState.REJECTED],
        ClaimState.REJECTED: [ClaimState.APPROVED],
    }

    def _is_admin(self, actor_role: object) -> bool:
        if actor_role is None:
            return False
        role_val = getattr(actor_role, "value", str(actor_role))
        return role_val in self.ADMIN_ROLES

    def get_allowed_transitions(
        self,
        current_state: ClaimState | None,
        actor_role: object | None = None,
    ) -> list[ClaimState]:
        """Return permitted target states from current_state for the given role."""
        allowed: list[ClaimState] = list(self.STANDARD_TRANSITIONS.get(current_state, []))
        if current_state is not None and self._is_admin(actor_role):
            overrides = self.OVERRIDE_TRANSITIONS.get(current_state, [])
            for target in overrides:
                if target not in allowed:
                    allowed.append(target)
        return allowed

    def can_transition(
        self,
        current_state: ClaimState | None,
        target_state: ClaimState,
        actor_role: object | None = None,
    ) -> bool:
        """Evaluate whether the transition from current_state to target_state is permitted."""
        allowed = self.get_allowed_transitions(current_state, actor_role=actor_role)
        return target_state in allowed

    def validate_transition(
        self,
        claim_id: str,
        current_state: ClaimState | None,
        target_state: ClaimState,
        actor_role: object | None = None,
    ) -> None:
        """
        Validate state transition; raises InvalidClaimStateException if forbidden.

        Raises:
            InvalidClaimStateException: If the transition path is invalid.
        """
        allowed = self.get_allowed_transitions(current_state, actor_role=actor_role)
        if target_state not in allowed:
            raise InvalidClaimStateException(
                claim_id=claim_id,
                current_state=current_state if current_state is not None else "None",
                attempted_target_state=target_state,
                allowed_target_states=allowed,
            )
