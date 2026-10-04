from collections.abc import Mapping
from datetime import date
from decimal import Decimal


class PolicyRepository:
    """Policy master data registry pre-seeded with domain test policies."""

    def __init__(self) -> None:
        self._policies: dict[str, dict[str, object]] = {
            "POL-MTR-1001": {
                "policy_number": "POL-MTR-1001",
                "line_of_business": "MOTOR",
                "status": "ACTIVE",
                "effective_date": date(2026, 1, 1),
                "expiry_date": date(2026, 12, 31),
                "sum_insured": Decimal("50000.00"),
                "deductible": Decimal("500.00"),
                "copay_percent": Decimal("0.00"),
                "fraud_threshold": 50,
                "version": 1,
            },
            "POL-HLT-2002": {
                "policy_number": "POL-HLT-2002",
                "line_of_business": "HEALTH",
                "status": "ACTIVE",
                "effective_date": date(2026, 1, 1),
                "expiry_date": date(2026, 12, 31),
                "sum_insured": Decimal("20000.00"),
                "deductible": Decimal("200.00"),
                "copay_percent": Decimal("10.00"),
                "fraud_threshold": 40,
                "version": 1,
            },
            "POL-LIF-3003": {
                "policy_number": "POL-LIF-3003",
                "line_of_business": "LIFE",
                "status": "ACTIVE",
                "effective_date": date(2026, 1, 1),
                "expiry_date": date(2026, 12, 31),
                "sum_insured": Decimal("100000.00"),
                "deductible": Decimal("0.00"),
                "copay_percent": Decimal("0.00"),
                "fraud_threshold": 50,
                "version": 1,
            },
            "POL-MTR-9999": {
                "policy_number": "POL-MTR-9999",
                "line_of_business": "MOTOR",
                "status": "EXPIRED",
                "effective_date": date(2025, 1, 1),
                "expiry_date": date(2025, 12, 31),
                "sum_insured": Decimal("50000.00"),
                "deductible": Decimal("500.00"),
                "copay_percent": Decimal("0.00"),
                "fraud_threshold": 50,
                "version": 1,
            },
            "POL-HLT-5555": {
                "policy_number": "POL-HLT-5555",
                "line_of_business": "HEALTH",
                "status": "LAPSED",
                "effective_date": date(2026, 1, 1),
                "expiry_date": date(2026, 12, 31),
                "sum_insured": Decimal("20000.00"),
                "deductible": Decimal("200.00"),
                "copay_percent": Decimal("10.00"),
                "fraud_threshold": 40,
                "version": 1,
            },
        }

    def get_policy(self, policy_number: str) -> Mapping[str, object] | None:
        """Retrieve policy details by policy number."""
        return self._policies.get(policy_number)

    def add_policy(self, policy_data: Mapping[str, object]) -> None:
        """Register or overwrite policy in repository."""
        pol_num = str(policy_data["policy_number"])
        self._policies[pol_num] = dict(policy_data)
