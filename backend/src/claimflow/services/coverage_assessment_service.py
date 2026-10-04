from datetime import datetime, timezone

from claimflow.database.models import CoverageAssessment
from claimflow.types.enums import ClaimType, CoverageReasonCode
from claimflow.types.exceptions import CoverageDefinitionNotFoundError


class CoverageAssessmentService:
    def __init__(self, policy_repository):
        self.policy_repository = policy_repository

    def assess_coverage(
        self,
        policy_id: str,
        claim_type: ClaimType,
        claim_incident_type: str | None = None
    ) -> CoverageAssessment:
        policy = self.policy_repository.get_policy(policy_id)
        if policy is None:
            raise CoverageDefinitionNotFoundError(policy_id)

        if self.check_exclusions(policy_id, claim_incident_type):
            return CoverageAssessment(
                is_covered=False,
                coverage_reason_code=CoverageReasonCode.POLICY_EXCLUSION,
                assessed_at=datetime.now(timezone.utc)
            )

        coverage = policy.get("coverage", [])
        is_covered = claim_type.value in coverage

        reason_code = (
            CoverageReasonCode.COVERAGE_VERIFIED
            if is_covered
            else CoverageReasonCode.CLAIM_TYPE_NOT_COVERED
        )

        return CoverageAssessment(
            is_covered=is_covered,
            coverage_reason_code=reason_code,
            assessed_at=datetime.now(timezone.utc)
        )

    def check_exclusions(self, policy_id: str, incident_type: str | None = None) -> bool:
        if incident_type is None:
            return False

        policy = self.policy_repository.get_policy(policy_id)
        if policy is None:
            return False

        exclusions = policy.get("coverage_exclusions", {})
        return incident_type in exclusions and exclusions[incident_type]
