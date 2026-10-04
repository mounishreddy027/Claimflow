import pytest

from claimflow.domain.state_machine import ClaimStateMachine
from claimflow.types.enums import ActorRole, ClaimState
from claimflow.types.exceptions import InvalidClaimStateException

pytestmark = pytest.mark.AC_10


def test_happy_path_lifecycle_progression() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-2026-00101"

    # None -> FILED
    assert sm.can_transition(None, ClaimState.FILED)
    sm.validate_transition(claim_id, None, ClaimState.FILED)

    # FILED -> UNDER_REVIEW
    assert sm.can_transition(ClaimState.FILED, ClaimState.UNDER_REVIEW)
    sm.validate_transition(claim_id, ClaimState.FILED, ClaimState.UNDER_REVIEW)

    # UNDER_REVIEW -> APPROVED
    assert sm.can_transition(ClaimState.UNDER_REVIEW, ClaimState.APPROVED)
    sm.validate_transition(claim_id, ClaimState.UNDER_REVIEW, ClaimState.APPROVED)

    # APPROVED -> SETTLED
    assert sm.can_transition(ClaimState.APPROVED, ClaimState.SETTLED)
    sm.validate_transition(claim_id, ClaimState.APPROVED, ClaimState.SETTLED)

    # SETTLED -> REOPENED
    assert sm.can_transition(ClaimState.SETTLED, ClaimState.REOPENED)
    sm.validate_transition(claim_id, ClaimState.SETTLED, ClaimState.REOPENED)


def test_valid_rejection_from_under_review() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-2026-00102"
    assert sm.can_transition(ClaimState.UNDER_REVIEW, ClaimState.REJECTED)
    sm.validate_transition(claim_id, ClaimState.UNDER_REVIEW, ClaimState.REJECTED)


def test_admin_override_transitions() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-2026-00103"

    # Admin can override APPROVED -> REJECTED
    assert sm.can_transition(
        ClaimState.APPROVED, ClaimState.REJECTED, actor_role=ActorRole.ADMIN
    )
    sm.validate_transition(
        claim_id, ClaimState.APPROVED, ClaimState.REJECTED, actor_role=ActorRole.ADMIN
    )

    # Admin can override REJECTED -> APPROVED
    assert sm.can_transition(
        ClaimState.REJECTED, ClaimState.APPROVED, actor_role=ActorRole.ADMIN
    )
    sm.validate_transition(
        claim_id, ClaimState.REJECTED, ClaimState.APPROVED, actor_role=ActorRole.ADMIN
    )

    # Non-admin cannot override APPROVED -> REJECTED
    assert not sm.can_transition(
        ClaimState.APPROVED, ClaimState.REJECTED, actor_role=ActorRole.ASSESSOR
    )
    with pytest.raises(InvalidClaimStateException):
        sm.validate_transition(
            claim_id,
            ClaimState.APPROVED,
            ClaimState.REJECTED,
            actor_role=ActorRole.ASSESSOR,
        )


def test_illegal_skip_transition_raises_exception() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-2026-00104"

    # Attempt FILED directly to APPROVED
    assert not sm.can_transition(ClaimState.FILED, ClaimState.APPROVED)
    with pytest.raises(InvalidClaimStateException) as exc_info:
        sm.validate_transition(claim_id, ClaimState.FILED, ClaimState.APPROVED)

    exc = exc_info.value
    assert exc.claim_id == claim_id
    assert exc.current_state == ClaimState.FILED
    assert exc.attempted_target_state == ClaimState.APPROVED
    assert ClaimState.UNDER_REVIEW in exc.allowed_target_states


def test_illegal_regression_raises_exception() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-2026-00105"

    # Attempt SETTLED back to UNDER_REVIEW
    assert not sm.can_transition(ClaimState.SETTLED, ClaimState.UNDER_REVIEW)
    with pytest.raises(InvalidClaimStateException):
        sm.validate_transition(claim_id, ClaimState.SETTLED, ClaimState.UNDER_REVIEW)


def test_illegal_transition_from_rejection() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-2026-00106"

    # Attempt REJECTED to SETTLED
    assert not sm.can_transition(ClaimState.REJECTED, ClaimState.SETTLED)
    with pytest.raises(InvalidClaimStateException):
        sm.validate_transition(claim_id, ClaimState.REJECTED, ClaimState.SETTLED)


def test_exhaustive_6x6_transition_matrix() -> None:
    sm = ClaimStateMachine()
    claim_id = "CLM-MATRIX-TEST"
    all_states = list(ClaimState)

    # Matrix: from each state to each target state
    # Expected valid paths with admin role:
    # 1. FILED -> UNDER_REVIEW
    # 2. UNDER_REVIEW -> APPROVED
    # 3. UNDER_REVIEW -> REJECTED
    # 4. APPROVED -> SETTLED
    # 5. APPROVED -> REJECTED (admin)
    # 6. REJECTED -> APPROVED (admin)
    # 7. SETTLED -> REOPENED
    valid_transitions = {
        (ClaimState.FILED, ClaimState.UNDER_REVIEW),
        (ClaimState.UNDER_REVIEW, ClaimState.APPROVED),
        (ClaimState.UNDER_REVIEW, ClaimState.REJECTED),
        (ClaimState.APPROVED, ClaimState.SETTLED),
        (ClaimState.APPROVED, ClaimState.REJECTED),
        (ClaimState.REJECTED, ClaimState.APPROVED),
        (ClaimState.SETTLED, ClaimState.REOPENED),
    }

    successful_count = 0
    forbidden_count = 0

    for current in all_states:
        for target in all_states:
            is_valid = (current, target) in valid_transitions
            can_do = sm.can_transition(current, target, actor_role=ActorRole.ADMIN)

            if is_valid:
                assert can_do, f"Expected {current.value} -> {target.value} to be valid"
                sm.validate_transition(
                    claim_id, current, target, actor_role=ActorRole.ADMIN
                )
                successful_count += 1
            else:
                assert not can_do, f"Expected {current.value} -> {target.value} to be invalid"
                with pytest.raises(InvalidClaimStateException):
                    sm.validate_transition(
                        claim_id, current, target, actor_role=ActorRole.ADMIN
                    )
                forbidden_count += 1

    # 6 * 6 = 36 total paths: 7 valid between the 6 states, 29 forbidden
    assert successful_count == 7
    assert forbidden_count == 29
