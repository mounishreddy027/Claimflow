from decimal import Decimal
from fastapi import APIRouter, Depends

from claimflow.api.dependencies import get_policy_repository
from claimflow.api.schemas import PolicyItemResponse
from claimflow.repositories.policy_repository import PolicyRepository
from claimflow.utils.financial import to_decimal

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


@router.get("", response_model=list[PolicyItemResponse])
def list_all_policies(
    policy_repo: PolicyRepository = Depends(get_policy_repository),
) -> list[PolicyItemResponse]:
    raw_policies = policy_repo.list_policies()
    results: list[PolicyItemResponse] = []
    for p in raw_policies:
        results.append(
            PolicyItemResponse(
                policyNumber=str(p["policy_number"]),
                lineOfBusiness=str(p["line_of_business"]),
                status=str(p["status"]),
                effectiveDate=p["effective_date"],  # type: ignore[arg-type]
                expiryDate=p.get("expiry_date"),  # type: ignore[arg-type]
                sumInsured=to_decimal(p["sum_insured"]),  # type: ignore[arg-type]
                deductible=to_decimal(p.get("deductible", Decimal("0.00"))),  # type: ignore[arg-type]
                copayPercent=to_decimal(p.get("copay_percent", Decimal("0.00"))),  # type: ignore[arg-type]
                fraudThreshold=int(p.get("fraud_threshold", 50)),  # type: ignore[arg-type]
            )
        )
    return results
