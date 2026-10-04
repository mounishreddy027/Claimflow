from datetime import date
from uuid import uuid4

import pytest

from claimflow.services.policy_service import PolicyService
from claimflow.types.exceptions import PolicyNotActiveException

pytestmark = pytest.mark.AC_02


@pytest.fixture
def policy_service() -> PolicyService:
    return PolicyService()


def test_policy_active_within_valid_date_range(policy_service: PolicyService) -> None:
    """
    Test 1: Policy is active when incident_date within [effective_date, expiry_date]
    effective: 2026-01-01, expiry: 2026-12-31, incident: 2026-06-01 -> is_active=true
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "MOTOR-12345",
        "effective_date": date(2026, 1, 1),
        "expiry_date": date(2026, 12, 31),
    }
    incident_date = date(2026, 6, 1)

    result = policy_service.validate_active(policy, incident_date)

    assert result is True


def test_policy_expired_rejects_with_policy_expired_reason(
    policy_service: PolicyService,
) -> None:
    """
    Test 2: Policy with past expiry_date rejected with POLICY_EXPIRED
    expiry: 2025-12-31, incident: 2026-06-01 -> POLICY_EXPIRED exception
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "MOTOR-54321",
        "effective_date": date(2025, 1, 1),
        "expiry_date": date(2025, 12, 31),
    }
    incident_date = date(2026, 6, 1)

    with pytest.raises(PolicyNotActiveException) as exc_info:
        policy_service.validate_active(policy, incident_date)

    assert exc_info.value.reason_code == "POLICY_EXPIRED"
    assert exc_info.value.policy_number == "MOTOR-54321"
    assert exc_info.value.incident_date == incident_date
    assert exc_info.value.effective_date == date(2025, 1, 1)
    assert exc_info.value.expiry_date == date(2025, 12, 31)


def test_policy_not_effective_rejects_with_policy_not_effective_reason(
    policy_service: PolicyService,
) -> None:
    """
    Test 3: Policy with future effective_date rejected with POLICY_NOT_EFFECTIVE
    effective: 2027-01-01, incident: 2026-06-01 -> POLICY_NOT_EFFECTIVE exception
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "MOTOR-99999",
        "effective_date": date(2027, 1, 1),
        "expiry_date": date(2027, 12, 31),
    }
    incident_date = date(2026, 6, 1)

    with pytest.raises(PolicyNotActiveException) as exc_info:
        policy_service.validate_active(policy, incident_date)

    assert exc_info.value.reason_code == "POLICY_NOT_EFFECTIVE"
    assert exc_info.value.policy_number == "MOTOR-99999"
    assert exc_info.value.incident_date == incident_date
    assert exc_info.value.effective_date == date(2027, 1, 1)
    assert exc_info.value.expiry_date == date(2027, 12, 31)


def test_policy_with_null_expiry_active_indefinitely(
    policy_service: PolicyService,
) -> None:
    """
    Test 4: Policy with NULL expiry_date active indefinitely if effective_date <= incident_date
    effective: 2026-01-01, expiry: NULL, incident: 2030-06-01 -> is_active=true
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "LIFETIME-001",
        "effective_date": date(2026, 1, 1),
        "expiry_date": None,
    }
    incident_date = date(2030, 6, 1)

    result = policy_service.validate_active(policy, incident_date)

    assert result is True


def test_policy_with_null_expiry_not_effective_yet(
    policy_service: PolicyService,
) -> None:
    """
    Test 5: Policy with NULL expiry_date inactive if effective_date > incident_date
    effective: 2027-01-01, expiry: NULL, incident: 2026-06-01 -> POLICY_NOT_EFFECTIVE
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "LIFETIME-002",
        "effective_date": date(2027, 1, 1),
        "expiry_date": None,
    }
    incident_date = date(2026, 6, 1)

    with pytest.raises(PolicyNotActiveException) as exc_info:
        policy_service.validate_active(policy, incident_date)

    assert exc_info.value.reason_code == "POLICY_NOT_EFFECTIVE"
    assert exc_info.value.policy_number == "LIFETIME-002"


def test_policy_active_on_boundary_effective_date(
    policy_service: PolicyService,
) -> None:
    """
    Test 6: Boundary test - incident_date == effective_date should be active
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "BOUNDARY-001",
        "effective_date": date(2026, 6, 1),
        "expiry_date": date(2026, 12, 31),
    }
    incident_date = date(2026, 6, 1)

    result = policy_service.validate_active(policy, incident_date)

    assert result is True


def test_policy_active_on_boundary_expiry_date(
    policy_service: PolicyService,
) -> None:
    """
    Test 7: Boundary test - incident_date == expiry_date should be active
    """
    policy = {
        "policy_id": str(uuid4()),
        "policy_number": "BOUNDARY-002",
        "effective_date": date(2026, 1, 1),
        "expiry_date": date(2026, 12, 31),
    }
    incident_date = date(2026, 12, 31)

    result = policy_service.validate_active(policy, incident_date)

    assert result is True


def test_error_response_includes_all_required_fields(
    policy_service: PolicyService,
) -> None:
    """
    Test 8: Error response includes policy_number, incident_date, effective_date, expiry_date
    """
    policy_number = "ERROR-TEST-001"
    effective_date = date(2026, 1, 1)
    expiry_date = date(2026, 6, 30)
    incident_date = date(2026, 12, 31)

    policy = {
        "policy_id": str(uuid4()),
        "policy_number": policy_number,
        "effective_date": effective_date,
        "expiry_date": expiry_date,
    }

    with pytest.raises(PolicyNotActiveException) as exc_info:
        policy_service.validate_active(policy, incident_date)

    error = exc_info.value
    assert error.policy_number == policy_number
    assert error.incident_date == incident_date
    assert error.effective_date == effective_date
    assert error.expiry_date == expiry_date
    assert error.reason_code == "POLICY_EXPIRED"
