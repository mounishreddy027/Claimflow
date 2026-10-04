import random
from decimal import Decimal

from claimflow.services.assessment_engine import AssessmentEngine
from claimflow.utils.financial import calculate_payable_amount, to_decimal


def test_standard_assessment_calculation() -> None:
    # Scenario 5.1: $4,000 claim, $10,000 sum insured, $500 deductible, $200 co-pay -> $3,300 payable
    claim_amount = Decimal("4000.00")
    sum_insured = Decimal("10000.00")
    deductible = Decimal("500.00")
    copay = Decimal("200.00")

    effective, gross_ded, net, payable = calculate_payable_amount(
        claim_amount=claim_amount,
        sum_insured=sum_insured,
        deductible=deductible,
        copay=copay,
    )

    assert effective == Decimal("4000.00")
    assert gross_ded == Decimal("700.00")
    assert net == Decimal("3300.00")
    assert payable == Decimal("3300.00")
    assert payable >= Decimal("0.00")


def test_sum_insured_cap_applied() -> None:
    # Scenario 5.2: $25,000 claim exceeds $15,000 sum insured, $1,000 deductible -> $14,000 payable
    claim_amount = Decimal("25000.00")
    sum_insured = Decimal("15000.00")
    deductible = Decimal("1000.00")
    copay = Decimal("0.00")

    effective, gross_ded, _, payable = calculate_payable_amount(
        claim_amount=claim_amount,
        sum_insured=sum_insured,
        deductible=deductible,
        copay=copay,
    )

    assert effective == Decimal("15000.00")
    assert gross_ded == Decimal("1000.00")
    assert payable == Decimal("14000.00")


def test_deductions_exceed_claim_clamps_to_zero_invariant() -> None:
    # Scenario 5.3: $400 claim, $500 deductible, $100 copay -> raw -$200, clamped to $0.00
    claim_amount = Decimal("400.00")
    sum_insured = Decimal("5000.00")
    deductible = Decimal("500.00")
    copay = Decimal("100.00")

    effective, gross_ded, net, payable = calculate_payable_amount(
        claim_amount=claim_amount,
        sum_insured=sum_insured,
        deductible=deductible,
        copay=copay,
    )

    assert effective == Decimal("400.00")
    assert gross_ded == Decimal("600.00")
    assert net == Decimal("-200.00")
    assert payable == Decimal("0.00")
    assert payable >= Decimal("0.00")


def test_percentage_copay_calculation() -> None:
    # Scenario 5.4: $10,000 claim, $20,000 sum insured, 10% copay, 0 deductible -> $9,000 payable
    engine = AssessmentEngine()
    assessment = engine.assess(
        claim_id="CLM-COP-1",
        claim_amount=Decimal("10000.00"),
        sum_insured=Decimal("20000.00"),
        deductible=Decimal("0.00"),
        copay_percent=Decimal("10.00"),
        assessed_by="assessor_1",
    )

    assert assessment.effective_claim == Decimal("10000.00")
    assert assessment.copay_applied == Decimal("1000.00")
    assert assessment.payable_amount == Decimal("9000.00")


def test_randomized_non_negative_invariants() -> None:
    # Property invariant test: across 200 randomized inputs, payable_amount is always >= 0.00
    random.seed(42)
    for _ in range(200):
        claim_amt = to_decimal(round(random.uniform(0, 100000), 2))
        sum_ins = to_decimal(round(random.uniform(100, 100000), 2))
        ded = to_decimal(round(random.uniform(0, 5000), 2))
        copay = to_decimal(round(random.uniform(0, 5000), 2))

        _, _, _, payable = calculate_payable_amount(
            claim_amount=claim_amt,
            sum_insured=sum_ins,
            deductible=ded,
            copay=copay,
        )
        assert payable >= Decimal("0.00"), f"Invariant violated: {payable} < 0"
        assert isinstance(payable, Decimal)
