import pytest
from datetime import datetime
from uuid import uuid4

from claimflow.services.coverage_assessment_service import CoverageAssessmentService
from claimflow.types.enums import ClaimType, CoverageReasonCode
from claimflow.types.exceptions import CoverageDefinitionNotFoundError


class MockPolicyRepository:
    def __init__(self, policies: dict):
        self.policies = policies

    def get_policy(self, policy_id: str):
        return self.policies.get(policy_id)


@pytest.fixture
def coverage_service():
    mock_repo = MockPolicyRepository({
        "motor_policy_with_coverage": {
            "policy_id": "motor_policy_with_coverage",
            "line_of_business": "MOTOR",
            "coverage": ["MOTOR"],
            "coverage_exclusions": {}
        },
        "health_policy_motor_only": {
            "policy_id": "health_policy_motor_only",
            "line_of_business": "HEALTH",
            "coverage": ["MOTOR"],
            "coverage_exclusions": {}
        },
        "motor_policy_with_exclusion": {
            "policy_id": "motor_policy_with_exclusion",
            "line_of_business": "MOTOR",
            "coverage": ["MOTOR"],
            "coverage_exclusions": {"pre_existing": True}
        },
        "health_policy_multi_coverage": {
            "policy_id": "health_policy_multi_coverage",
            "line_of_business": "HEALTH",
            "coverage": ["MOTOR", "HEALTH"],
            "coverage_exclusions": {}
        },
        "health_policy_no_coverage": {
            "policy_id": "health_policy_no_coverage",
            "line_of_business": "HEALTH",
            "coverage": [],
            "coverage_exclusions": {}
        }
    })
    return CoverageAssessmentService(mock_repo)


class TestCoverageAssessmentBasic:
    def test_motor_claim_covered_by_motor_policy(self, coverage_service):
        result = coverage_service.assess_coverage("motor_policy_with_coverage", ClaimType.MOTOR)
        assert result.is_covered is True
        assert result.coverage_reason_code == CoverageReasonCode.COVERAGE_VERIFIED
        assert result.assessed_at is not None

    def test_health_claim_not_covered_by_motor_only_policy(self, coverage_service):
        result = coverage_service.assess_coverage("health_policy_motor_only", ClaimType.HEALTH)
        assert result.is_covered is False
        assert result.coverage_reason_code == CoverageReasonCode.CLAIM_TYPE_NOT_COVERED

    def test_motor_claim_rejected_due_to_exclusion(self, coverage_service):
        result = coverage_service.assess_coverage("motor_policy_with_exclusion", ClaimType.MOTOR, claim_incident_type="pre_existing")
        assert result.is_covered is False
        assert result.coverage_reason_code == CoverageReasonCode.POLICY_EXCLUSION

    def test_multiple_coverages_motor_claim_covered(self, coverage_service):
        result = coverage_service.assess_coverage("health_policy_multi_coverage", ClaimType.MOTOR)
        assert result.is_covered is True
        assert result.coverage_reason_code == CoverageReasonCode.COVERAGE_VERIFIED

    def test_multiple_coverages_health_claim_covered(self, coverage_service):
        result = coverage_service.assess_coverage("health_policy_multi_coverage", ClaimType.HEALTH)
        assert result.is_covered is True
        assert result.coverage_reason_code == CoverageReasonCode.COVERAGE_VERIFIED

    def test_claim_rejected_no_coverages_defined(self, coverage_service):
        result = coverage_service.assess_coverage("health_policy_no_coverage", ClaimType.MOTOR)
        assert result.is_covered is False
        assert result.coverage_reason_code == CoverageReasonCode.CLAIM_TYPE_NOT_COVERED


class TestCoverageAssessmentIdempotency:
    def test_idempotency_same_inputs_identical_output(self, coverage_service):
        result1 = coverage_service.assess_coverage("motor_policy_with_coverage", ClaimType.MOTOR)
        result2 = coverage_service.assess_coverage("motor_policy_with_coverage", ClaimType.MOTOR)
        assert result1.is_covered == result2.is_covered
        assert result1.coverage_reason_code == result2.coverage_reason_code


class TestCoverageAssessmentDeterminism:
    def test_determinism_multiple_calls_same_result(self, coverage_service):
        results = [
            coverage_service.assess_coverage("motor_policy_with_coverage", ClaimType.MOTOR)
            for _ in range(5)
        ]
        for result in results[1:]:
            assert result.is_covered == results[0].is_covered
            assert result.coverage_reason_code == results[0].coverage_reason_code


class TestCoverageAssessmentErrorHandling:
    def test_coverage_definition_not_found_raises_error(self, coverage_service):
        with pytest.raises(CoverageDefinitionNotFoundError):
            coverage_service.assess_coverage("nonexistent_policy", ClaimType.MOTOR)


class TestCheckExclusionsMethod:
    def test_check_exclusions_returns_true_for_excluded_incident(self, coverage_service):
        is_excluded = coverage_service.check_exclusions("motor_policy_with_exclusion", "pre_existing")
        assert is_excluded is True

    def test_check_exclusions_returns_false_for_non_excluded_incident(self, coverage_service):
        is_excluded = coverage_service.check_exclusions("motor_policy_with_coverage", "pre_existing")
        assert is_excluded is False
